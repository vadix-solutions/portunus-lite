#!/usr/bin/env bash
count=${COUNT:-5}

# DONT CHANGE THIS - Fixture dependant on this value (modify that too if required)
name_prefix=${PREFIX:-sshd_container_}

function name(){
    echo ${name_prefix}$1
}

function create_container(){
    name=$(name $1)
    echo "Creating $name"
    docker run -d --name $name --network=portunus-lite_default rastasheep/ubuntu-sshd:14.04 &
}

function kill_container(){
    name=$(name $1)
    echo "Killing $name"
    docker rm -f $name &
}

function create_containers(){
    for i in $(seq 1 $count); do
        create_container $i
    done
}

function list_ips(){
    echo "Container IPS:"
    for i in $(seq 1 $count); do
        name=$(name $i)
        docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $name
    done
}

function kill_containers(){
    for i in $(seq 1 $count); do
        kill_container $i
    done
}

function verify_account_loop(){
  while true; do
    # Check to continue loop
    read -p "Quit? " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
      break
    fi
  done
}

function main(){
    echo "Creating $count local temporary sshd containers"
    read -p "Press enter to continue or Ctrl+C to exit"
    create_containers
    echo "Waiting 3 seconds"
    sleep 3
    list_ips
    # echo "Loading platform fixture in Identity System"
    # create_platform
    verify_account_loop
    read -p "Press enter to delete temporary containers"
    kill_containers
    wait
}

main
