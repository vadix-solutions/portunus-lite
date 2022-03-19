Demo Script

#------------------------
TALKING POINTS
#------------------------

Every function of Portunus has been carefully crafted to ensure the least amount of database interaction is required. During our journey into
IAM we discovered a lot of the existing solutions had terrible difficulty with complex/large datasets being parsed by the application. Understanding
those challenges, Portunus is more capable of handling large amounts of data quickly.



Know your audience. Leading IAM solutions today largely require a set of developers work in tandem with the engineers who will be responsible for the system.
Portunus enables your engineers to develop using already known skillsets with easy and quick to create custom tasks and interfaces meaning quicker deployment
of new features and a much lower cost to the business.


One massive  gap we've noticed from existing solutions is the dependance of an auxilary service or application which is used for host idenfication/discovery. Portunus
has addresses this by allowing users of the system to define host ranges which will then periodically identify those servers and insert them into the appropriate Access Domain

# AGENT NAME: agent_regional_us_east

# Scale agent in US
./fargate --region us-east-1 --cluster agent service scale agent 1

# Scale US SSH containers
./fargate --region us-east-1 --cluster ssh-containers service scale ssh-containers 20
# Scale EU SSH containers
./fargate --region eu-west-1 --cluster ssh-containers service scale sshd 20

# Review Container counts
./fargate --region eu-west-1 --cluster ssh-containers service list
./fargate --region us-east-1 --cluster ssh-containers service list

# Host Scan
Run a host scan in the Admin section

>>> How to show its happened?

# Show Access fixed/reconciled

>>> Scale agents?

# Increase Host Count in both regions
# Run a collect?

# Inspect the data
