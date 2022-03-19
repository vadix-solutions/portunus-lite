##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import base64
import json
import logging

import celery.states as celery_states
from celery.result import AsyncResult
from celery.utils import uuid
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from django.conf import settings
from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation,
)
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import PermissionDenied
from django.db import models
from django.urls import reverse

from vdx_id.celery import app
from vdx_id.util.arg_search import (
    UnresolvableArgException,
    resolve_templatevar_in_obj,
)
from vdx_id.util.task_util import chunks

logger = logging.getLogger("vdx_id.%s" % __name__)


class CeleryTaskMetaState(object):
    PENDING = 0
    STARTED = 1
    RETRY = 2
    FAILURE = 3
    SUCCESS = 4

    @classmethod
    def lookup(cls, state):
        return getattr(cls, state)

    def __contains__(self, state):
        return hasattr(self, state)


class ViAgent(models.Model):
    active = models.BooleanField(default=False)

    # Metadata
    agent_name = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=40)
    link_date = models.DateTimeField(null=True, blank=True)
    public_key = models.TextField()
    queue_name_override = models.CharField(
        max_length=80, blank=True, null=True
    )

    @property
    def queue_name(self):
        if self.queue_name_override:
            return self.queue_name_override
        else:
            return self.agent_name

    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"

    def __str__(self):
        return "%s (Active:%s)" % (self.agent_name, self.active)


# TODO: Deploy interface from Portunus to remote Agents
class ViAgentInterface(models.Model):
    interface_id = models.CharField(max_length=255, unique=True)
    code_fingerprint = models.CharField(max_length=255)
    task_signature = models.CharField(max_length=255, null=True)
    api = JSONField(default=dict, blank=True)

    complete_api_interfaces = ["collect_access"]

    default_capabilities = JSONField(
        default=dict,
        help_text="Default mapping of capability->interface_function",
    )

    agents = models.ManyToManyField(
        ViAgent, related_name="agent_interface_set"
    )

    date_created = models.DateTimeField("created", auto_now_add=True)
    date_updated = models.DateTimeField("last_updated", auto_now=True)

    class Meta:
        verbose_name = "Agent Interface"
        verbose_name_plural = "Agent Interfaces"

    def __str__(self):
        return self.interface_id

    def get_apicall_args_kwargs(self, api_command):
        required_task_args = self.api[api_command]["required"]
        optional_task_args = self.api[api_command]["optional"]
        required_connection_args = self.api["CONNECTION"]["required"]
        optional_connection_args = self.api["CONNECTION"]["optional"]
        args = required_task_args + required_connection_args
        kwargs = optional_task_args + optional_connection_args
        return args, kwargs


class AgentApiTask(models.Model):
    """Generates batches of Celery tasks for the Agents.
    Given an API call and any extra arguments, create a model instance.
    The model will have child task chunks which track the tasks sent to
    to groups (batches) of servers.
    Multiple 'jobs' are sent in a single Celery task to reduce thrashing on
    the message bus for situations with lots of servers.
    """

    # Even though AccessDomain collections are chords, we can store the API
    #   tasks in one of these objects. The collect_access API call is still
    #   created, but we can chord against the celery tasks anyway
    api_call = models.CharField(max_length=255)
    access_domain = models.ForeignKey(
        "id_infra.ViAccessDomain", on_delete=models.CASCADE, null=True
    )

    tasks_complete = models.BooleanField(default=False)
    tasks_successful = models.BooleanField(default=False)
    server_pks = JSONField(null=True, blank=True)

    # Attributes for a Generic relationship
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agent API Task"
        verbose_name_plural = "Agent API Tasks"

    def __str__(self):
        return self.api_call

    @property
    def celery_task_list(self):
        return list(
            str(task_id)
            for task_id in AgentCeleryTask.objects.filter(
                source_api_task=self
            ).values_list("task_id", flat=True)
        )

    def get_absolute_url(self):
        return reverse(
            "api:id_infra:agent_apitask-detail", kwargs={"pk": self.pk}
        )

    def generate_celery_tasks(self, source_object, mapped_args):
        """Create an array of celery task signatures
        Iterates through 'provided_args' dict of {arg:'{reference}}
        Resolves each 'reference' so that 'arg' has a value.
        Gets the API Args/Kwargs.
        Iterates over all Agent:[Server],
            resolving all required args for each server and agent.
        Optional arguments are attempted to be retrieved also.
        If all required args are satisfied, Celery task generated.
        """
        # Get a dict of required/optional arguments from the interface
        arg_d, kwarg_d = self.access_domain.get_api_param_dicts(self.api_call)

        # Simple function to update d1 using matching keys from d2
        def insert_matched_key(d1, d2):
            for k in d1.keys() & d2.keys():
                d1[k] = d2[k]

        # Wrapped func to resolve keyworded values in a dict against obj
        def fulfil_args(arg_dict, object, search_properties=False, **kwargs):
            """Given a dictionary containing api_param:templated_value
            Search the object for a solution for templated_value"""
            unresolvable_args = []
            for param_key, param_val in arg_dict.items():

                if param_val is None:
                    if search_properties:
                        param_val = "{properties.%s}" % param_key
                    else:
                        continue

                try:
                    resolved_param = resolve_templatevar_in_obj(
                        object, param_val, **kwargs
                    )
                except UnresolvableArgException:
                    unresolvable_args.append(param_key)

                if resolved_param:
                    arg_dict[param_key] = resolved_param
            # Remove any args that can't be resolved
            for param_key in unresolvable_args:
                logger.warning(f"Removing {param_key} - unresolvable")
                del arg_dict[param_key]

        # Resolve args provided into required/optional args
        insert_matched_key(arg_d, mapped_args)
        insert_matched_key(kwarg_d, mapped_args)

        # Partial early solve of args
        # (to prevent extra reads while iterating on servers)
        fulfil_args(arg_d, source_object, search_properties=True)
        fulfil_args(kwarg_d, source_object, search_properties=True)

        # Now iterate over agent: [servers] and generate the tasks required
        celery_tasks = []
        agent_server_gen = self.access_domain.yield_agent_server_sets(
            server_pks=self.server_pks
        )
        for agent, agent_servers in agent_server_gen:

            agent_actions = []  # A list of dicts for agent job parameters
            for server in agent_servers:
                # Make a copy of the partial resolved args/kwargs
                task_args = arg_d.copy()
                task_kwargs = kwarg_d.copy()

                # Set the server in this object for resolving
                source_object.server = server
                fulfil_args(task_args, source_object, raise_unresolved=True)
                fulfil_args(task_kwargs, source_object)
                # Raise KeyError if some args are not satisfied
                if None in arg_d.values():
                    missing_args = [
                        arg for arg, val in arg_d.items() if val is None
                    ]
                    raise KeyError(
                        f"Cannot create task. Unresolved: {missing_args}"
                    )
                # Now that we have resolved enough args, store in action list
                task_kwargs.update(task_args)
                agent_actions.append(task_kwargs)

            celery_tasks += self.chunked_signatures(agent, agent_actions)
        return celery_tasks

    def chunked_signatures(self, agent, agent_actions):

        task_chunks = settings.AGENT_TASK_SEGMENTATION
        actions_per_chunk = -(len(agent_actions) // -task_chunks)

        # Create celery task for a chunk of servers for agent host
        agent_task_signatures = []
        for action_batch in chunks(agent_actions, actions_per_chunk):
            # Encrypt the array of arguments using agent pubkey
            action_batch = self.encrypt_action_batch(agent, action_batch)
            # Generate celery signature
            agent_task_sig = app.signature(
                self.access_domain.interface.task_signature,
                args=(
                    self.access_domain.interface.interface_id,
                    self.api_call,
                    action_batch,
                ),
                options=({"task_id": uuid()}),
            ).set(queue=agent.queue_name)
            agent_task_signatures.append(agent_task_sig)
        return agent_task_signatures

    @staticmethod
    def encrypt_action_batch(agent, action_batch):
        """Encrypts a array of worker calls for transmission"""
        recipient_key = RSA.import_key(agent.public_key)
        session_key = get_random_bytes(16)

        # Encrypt the session key with the public RSA key
        cipher_rsa = PKCS1_OAEP.new(recipient_key)
        enc_session_key = cipher_rsa.encrypt(session_key)

        # Convert payload to b64 bytes
        bytestr = json.dumps(action_batch).encode("utf-8")

        # Encrypt the data with the AES session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX)
        ciphertext, tag = cipher_aes.encrypt_and_digest(bytestr)

        # Send back full cipher_msg
        cipher_msg = base64.b64encode(
            enc_session_key + cipher_aes.nonce + tag + ciphertext
        )
        return cipher_msg

    def link_celery_tasks(self, celery_task_ids):
        agent_celery_tasks = [
            AgentCeleryTask(source_api_task=self, task_id=ctask_id)
            for ctask_id in celery_task_ids
        ]
        AgentCeleryTask.objects.bulk_create(agent_celery_tasks)

    def update_state(self, complete_empty=False):
        child_task_states = AgentCeleryTask.objects.filter(
            source_api_task=self
        ).values_list("state", flat=True)
        if not (child_task_states):
            if not complete_empty:
                return
            else:
                self.tasks_complete = True
                self.save(update_fields=["tasks_complete"])
                return

        state_strings = [
            AgentCeleryTask.STATES[s_id][1] for s_id in child_task_states
        ]
        logger.info(
            f"API-Task {self.pk}-{self} celery states: {state_strings}"
        )
        if min(child_task_states) >= CeleryTaskMetaState.FAILURE:
            self.tasks_complete = True
        if min(child_task_states) == CeleryTaskMetaState.SUCCESS:
            self.tasks_successful = True
        self.save(
            update_fields=["tasks_complete", "tasks_successful", "updated"]
        )


class AgentCeleryTask(models.Model):
    STATES = (
        (CeleryTaskMetaState.PENDING, celery_states.PENDING),
        (CeleryTaskMetaState.STARTED, celery_states.STARTED),
        (CeleryTaskMetaState.RETRY, celery_states.RETRY),
        (CeleryTaskMetaState.FAILURE, celery_states.FAILURE),
        (CeleryTaskMetaState.SUCCESS, celery_states.SUCCESS),
    )

    source_api_task = models.ForeignKey(
        AgentApiTask, null=True, on_delete=models.CASCADE
    )
    # Celery task ID
    task_id = models.CharField(max_length=255, unique=True)
    state = models.PositiveIntegerField(
        choices=STATES, default=CeleryTaskMetaState.PENDING
    )
    exception = models.TextField(default="")
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.source_api_task} ({self.STATES[self.state][1]})"

    class Meta:
        verbose_name = "Agent Celery Task"
        verbose_name_plural = "Agent Celery Tasks"

    def manually_update_state(self):
        """Called if a task is not updated by celery_monitor"""
        state = AsyncResult(self.task_id).state
        self.state = CeleryTaskMetaState.lookup(state)
        logger.info(f"Manually UPD CelTask({self.task_id}) state={state}")
        self.save(update_fields=["state"])


class AgentTaskMixin(models.Model):
    """Mixin for any access-object class.
    Provides a function to invoke a named API call (from AgentInterface).
    Will create an instance of AgentApiTask which tracks the corresponding
    Celery tasks (which each contain one or more jobs for the Agent).
    E.g. 20 servers may result in 5 celery tasks, each with 4 'agent jobs'.
    """

    agent_tasks = GenericRelation(AgentApiTask)

    class Meta:
        abstract = True

    def perform_capability(
        self, capability_name, server_pks=None, **cap_kwargs
    ):
        if self.access_domain.user_source_authority:
            raise PermissionDenied(
                "AccessDomain is User Data Source - "
                "you cannot perform write operations."
            )

        # Build args from kwargs and the collection_data
        # Maintain Order here - important!
        task_kwargs = cap_kwargs.copy()
        task_kwargs.update(self.collection_data)
        task_kwargs.update(self.properties)

        # Then try generate the tasks for this capability
        agent_api_task, mapped_args = self.generate_capability_task(
            self.access_domain,
            capability_name,
            task_kwargs,
            server_pks=server_pks,
        )
        logger.info(f"Creating AgentAPI task {agent_api_task} {task_kwargs}")
        celery_tasks = agent_api_task.generate_celery_tasks(self, mapped_args)
        # Run all the tasks
        async_results = [ctask.apply_async() for ctask in celery_tasks]
        # Create child task objects for each celery task (link to this)
        agent_api_task.link_celery_tasks(async_results)
        return agent_api_task

    def generate_capability_task(
        self, acc_domain, capability_name, task_kwargs, server_pks=None
    ):
        """Creates an AgentApiTask for the 'capability_name' requested.
        Gets a capability definition (contains API call and arg mapping).
        Retrieves the mapping of argument:reference in capability, merges
        with task_kwargs.
        AgentApiTask can then use this to resolve required arguments from API
        """
        # Get the API call and the mapped arguments for it
        api_call, mapped_args = acc_domain.get_capability(
            self.capability_category, capability_name
        )

        # Add the kwargs from this function in case they are satisfy args
        mapped_args.update(task_kwargs)

        # Create a new AgentApiTask, and make it generate its child tasks
        agent_api_task = AgentApiTask.objects.create(
            api_call=api_call,
            access_domain=acc_domain,
            content_object=self,
            server_pks=server_pks,
        )

        return agent_api_task, mapped_args
