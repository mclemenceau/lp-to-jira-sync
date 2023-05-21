# Launchpad to Jira sync

## Definitions
*LaunchPad bugs* : The bugs we are interested in here are all the bugs in
Launchpad with a specific tag that are still active in Launchpad.
These could affect any packages in the ubuntu project or individual projects
(subiquity, netplan, apport)

*Launchpad bug tasks* : each bug in Launchpad can have one or multiple tasks. A
task defines what package is affected by this bug for what series of Ubuntu. 

*active bug tasks* : In LaunchPad API (bug_task.is_complete = False)

## Specification
1. For each bug tagged, we will synchronize each affected package with ts active
tasks if the package is subscribed by a specific team
3. There could be more than one Jira ticket per Launchpad Bug
4. These Jira Bugs title will be as follows
- LP#XXXXXX [affected package] title …….
4. The synchronization will be one-way from Launchpad to Jira
5. Launchpad will remain the Source of Truth for bug status
6. The autosync will periodically compare all the bug/package pairs in Launchpad
with all the bug/package pairs in Jira
  1. The bug is on both lists and might just need to be synced
  2. The bug is only in Launchpad and needs to either be created in Jira or
  resurrected if it would have been set to Done prematurely
  3. The bug is only in Jira and as a result need to be closed (Move to Done)
    1. The bug in LP could have lost its tag
	2. The bug / package tasks in LP are all complete
	3. The bug never had a tag and would need one to be in Jira
7. The auto sync will synchronize
  1. LP title will be automatically updated in Jira
  2. The bug importance will be reflected in Jira as following
    - 'Unknown' ->  Medium 
	- 'Undecided' : Low
	- 'Critical' : 'Highest'
	- 'High' : 'High'
	- 'Medium' : 'Medium'
	- 'Low' : 'Low'
	- 'Wishlist' : 'Lowest'
