import argparse

from lp_to_jira_sync.sync_config import SyncConfig


jira_priorities_mapping = {'Unknown': 'Medium',
                           'Undecided': 'Low',
                           'Critical': 'Highest',
                           'High': 'High',
                           'Medium': 'Medium',
                           'Low': 'Low',
                           'Wishlist': 'Lowest'}


# Create a Jira Entry from a LP bugset (list of tasks relevant to a bug and
# package)
def lp_to_jira_bug(sync_bug_id, sync_bug_tasks, config):
    """Create JIRA issue at project_id for a given Launchpad bug"""

    if is_bug_in_jira(config.jira, sync_bug_id, config.project):
        return

    lpbug = sync_bug_tasks[0].bug

    issue_dict = {
        'project': config.project,
        'summary': 'LP#{} [{}] {}'.format(
            sync_bug_id[0], sync_bug_id[1],
            lpbug.title),
        'description': lpbug.description,
        'issuetype': {'name': 'Bug'}
    }

    jira_issue = config.jira.create_issue(fields=issue_dict)

    # Adding a link to the Launchpad bug into the JIRA entry
    link = {
        'url': lpbug.web_link,
        'title': 'Launchpad Link',
        'icon': {'url16x16': 'https://bugs.launchpad.net/favicon.ico'}
    }
    config.jira.add_simple_link(jira_issue, object=link)

    return jira_issue


def get_bug_id(summary):
    "Extract the bug id from a jira title which would include LP#"
    id = ""

    if summary and "LP#" in summary:
        for char in summary[summary.find("LP#")+3:]:
            if char.isdigit():
                id = id + char
            else:
                break

    return id


def get_bug_pkg(summary):
    # Extract the bug affected package from a jira title
    # which would include LP#"
    id = ""

    if summary and "LP#" in summary and '[' in summary:
        return summary[summary.index('[')+1:summary.index(']')]

    return id


def is_bug_in_jira(jira, bug_id, project_id):
    """Checks Jira for the same ID as the Bug you're trying to import"""

    request = "project = \"{}\" AND summary ~ '\"LP#{} [{}]\"'".format(
        project_id, bug_id[0], bug_id[1])

    existing_issue = jira.search_issues(request)

    if existing_issue:
        return existing_issue[0]

    return None


# BugTask Functions
def lp_assignee(bugtasks):
    if not bugtasks:
        return None

    for task in bugtasks:
        if task.assignee_link:
            return task.assignee_link[task.assignee_link.index('~')+1:]

    return None


def lp_status(bugtasks):
    if not bugtasks:
        return None
    for task in bugtasks:
        print(task.status)

    return None


def lp_importance(bugtasks):
    if not bugtasks:
        return None
    # we return the first task importance which is the highest other than None
    return bugtasks[0].importance


def checklist(bugtasks):
    if not bugtasks:
        return None

    checklist_str = "# Default checklist"
    for task in bugtasks:
        checked = "x" if task.is_complete else ""
        checklist_str = checklist_str + "\n* [{}] {} - {} - {}".format(
            checked,
            task.title.split(":")[0].split("in ")[1],
            task.status,
            task.importance)

    # No Checklist if only one serie impacted
    if len(bugtasks) > 1:
        return checklist_str

    return None

# return the list of taskset in the following format
# taskset is a relevant set of task for a bug/package combination
#
# {(bug_id, package):[lp tasks]}


def refine_tasks(tasks, config):
    results = {}
    for task in tasks:
        # It is much more efficient to parse the task title than accessing the
        # LP API
        title = task.title.split()
        name = title[3]
        # remove sneaky trailing ':'
        if name[-1] == ':':
            name = name[:-1]

        # Create the taskset identifier
        pair = (int(title[1][1:]), name)
        if pair not in results:
            results[pair] = []

        # If package is in Ubuntu and belong to the relevant team
        if ("(Ubuntu" in task.bug_target_name
                and name in config.restricted_pkgs):
            results[pair].append(task)
        elif name in config.special_packages:
            results[pair].append(task)
        else:
            del results[pair]

    # remove bugtasks where all the task are Fix Released
    results_copy = results.copy()
    for bugtask in results:
        complete = True
        for task in results[bugtask]:
            if task.status != 'Fix Released':
                complete = False
                break
        if complete:
            del results_copy[bugtask]

    return results_copy


def find_bugs_in_jira_project(jira_api, project):
    if not jira_api or not project:
        return {}

    # Get JIRA issues in batch of 50
    issue_index = 0
    issue_batch = 50

    found_issues = {}

    while True:
        start_index = issue_index * issue_batch
        request = "project = {} " \
            "AND summary ~ \"LP#\" " \
            "AND status not in (Done, \"Rejected\")""".format(project)
        issues = jira_api.search_issues(request, startAt=start_index)

        if not issues:
            break

        issue_index += 1

        # For each issue in JIRA with LP# in the title
        for issue in issues:
            summary = issue.fields.summary
            lpbug_id = get_bug_id(summary)
            lppkg = get_bug_pkg(summary)

            if lpbug_id:
                found_issues[(int(lpbug_id), lppkg)] = issue

    return found_issues


def jira_assignee(issue):
    if not issue:
        return None

    return issue.fields.assignee


def jira_priority(issue):
    if not issue:
        return None

    return issue.fields.priority.name


def sync(taskset, issue, config):
    if not taskset or not issue or not config:
        return False

    bug = taskset[0].bug

    # Title
    # Title may change in LP and we want to make sure
    # it match the title in Jira
    # TODO: write sync title function
    lp_title = bug.title
    jira_title = issue.fields.summary

    if lp_title not in jira_title:
        print("-> Syncing title for {}".format(issue.key))
        jira_title = jira_title[:jira_title.index(']')+2] + lp_title
        config.jira.add_comment(
            issue,
            ('{{jira-bot}} Fixed out of sync title with LP: #%s') % (bug.id)
        )
        issue.update(summary=jira_title)

    # Status
    # At this stage at a minimum the issue should be in Triaged but other
    # status could be possible in the future Sponsoring Needed could be
    # selected if Ubuntu Sponsor team is subsribed
    # In Progress ?
    # TODO write sync status function
    if False:
        # disabling this code for now as I'm not sure it is worth it
        # it slows the execuition for all the bug and a bug might be
        # subscriobed by ubuntu sponsors for another task than the one we
        # care about
        sponsor = 'https://api.launchpad.net/devel/~ubuntu-sponsors'
        if sponsor in [x['person_link']
                       for x in bug.subscriptions.entries]:
            print(" - Fixing status to Sponsoring Needed")
            comment = ('{{jira-bot}} ubuntu sponsors team is subscribed '
                       'to the bug which means it should move to Sponsoring '
                       ' Needed')
            config.jira.add_comment(issue, comment)
            config.jira.transition_issue(
                issue,
                transition='Sponsoring Needed'
            )

    # sync Status
    if issue.fields.status.name == 'Untriaged':
        print("-> Updating Status for {} to Triaged".format(issue.key))
        comment = ('{{jira-bot}} {} should be in '
                   'Triaged'.format(config.tag)
        config.jira.add_comment(issue, comment)
        config.jira.transition_issue(
            issue,
            transition='All'
        )

    # Sync Checklist
    # If a bug impact a package on multiple serie, we create a Checklist on the
    # Jira issue that list all series
    checkstr = checklist(taskset)
    jiracheckstr = issue.fields.customfield_10039
    if checkstr and checkstr != jiracheckstr:
        print("-> Updating Checklist for {}".format(issue.key))
        issue.update(fields={'customfield_10039': checkstr})

    # Assignee
    # If a team mapping has been provided we can look at for a match between
    # The LaunchPad bug assignee and the Jira account available
    # TODO create a standalone function for assignee actions
    if config.team_ids:
        lp_who = lp_assignee(taskset)
        jira_who = jira_assignee(issue)
        if lp_who in config.team_ids.keys():
            # Someone from specific team is assigned to the bug
            # But nobody is assigned in Jira
            # In that case we assign the bug the same person from LP
            if not jira_who:
                account = config.team_ids[lp_who]['id']
    #            issue.update(assignee={'id':account})
                print("-> Updating assignee for {} to {}".format(
                    issue.key,
                    config.team_ids[lp_who]['name']))

    # Importance
    # We should reflect the launchpad bug Priority with the Jira issue priority
    importance = jira_priorities_mapping[lp_importance(taskset)]
    priority = jira_priority(issue)
    if importance != priority:
        print("-> Syncing Priority for {} to {}".format(
            issue.key, importance))
        issue.update(priority={"name": importance})


def process_issues(all_tasks, all_issues, config):
    # Between All subscribed bug in LP and all bug imported in JIRA, there's
    # 3 Groups:
    #   A: bug are active in both LP and Jira
    #   B: bugs only active in LP
    #   C: bugs only active in Jira

    # an active bug in Jira has a status different than Done or Rejected
    # an active bug in LP is not Fix Released and Invalid

    # Group A
    #   -> Check if they are in sync

    # Group B
    #   -> Add them to JIRA, and sync

    # Group C
    #   Could have been unsubscribed in LP, or added in JIRA and multiple
    #   actions are possible
    #   For now we will go the hard way and REJECT any bug in Jira that isn't
    #   tagged 

    for bugset in all_tasks:
        if bugset in all_issues:
            # bug are active in both LP and Jira
            print("A: LP: #{} [{}] is in Jira as {}"
                  .format(bugset[0], bugset[1], all_issues[bugset].key))
            if not config.dry_run:
                sync(
                    all_tasks[bugset],
                    all_issues[bugset],
                    config)
            del all_issues[bugset]
        else:
            # bugs only active in LP
            print("B: LP: #{} [{}] is not active in Jira"
                  .format(bugset[0], bugset[1]))

            # Checking if the bug is inactive in Jira
            jira_issue = is_bug_in_jira(config.jira, bugset, config.project)
            if jira_issue and (str(jira_issue.fields.status)
                               in ('Done', 'Rejected')):
                comment = ("""
                    This Bug is still active and tagged {} in LP.
                    It wil be moved back to the Backlog as Triaged.
                    If no work is necessary or the bug isn't relevant anymore,
                    please untag the bug in LP.
                    """.format(config.tag))
                if not config.dry_run:
                    config.jira.transition_issue(
                        jira_issue,
                        # All = Triaged
                        transition='All'
                    )
                    config.jira.add_comment(jira_issue, comment)
            else:
                if not config.dry_run:
                    jira_issue = lp_to_jira_bug(
                                    bugset, all_tasks[bugset], config)
                else:
                    pass

            if not config.dry_run:
                sync(
                    all_tasks[bugset],
                    jira_issue,
                    config)

    for issue in all_issues:
        # bugs only active in Jira
        print("C: LP: #{} [{}] is in Jira as {} but not tagged in LP".format(
            issue[0], issue[1],  all_issues[issue].key))
        comment = ('LP: #{} is either not tagged {} or'
                   ' active at this time. '
                   'Moving issue to Done. If this is incorrect, check the '
                   'status of the bug in LaunchPad.').format(
                    issue[0], config.tag)
        if not config.dry_run:
            config.jira.transition_issue(all_issues[issue], transition="Done")
            config.jira.add_comment(all_issues[issue], comment)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="A script"
    )

    opts = parser.parse_args(args)
    # TODO These will be command line parameters soon
    config = SyncConfig(
        project="FS",
        lp_tag="todo",
        lp_team="team",
        special_packages=['subiquity', 'netplan', 'apport'],
        dry_run=False)

    print("Found {} subscribed packages by team {}"
          .format(len(config.restricted_pkgs), config.team))

    print("Retrieving all tasks from bug with {} tag".format(config.tag))
    statuses = ['Triaged',
                'Fix Committed',
                'New',
                'In Progress',
                'Incomplete',
                'Confirmed',
                'Fix Released']

    tasks = config.lp.bugs.searchTasks(tags=config.tag, status=statuses)
    print(" - Found {} () bug's task{} in LaunchPad".format(
        len(tasks), "s" if len(tasks) > 1 else "", config.tag)
    )

    # Remove tasks that affects non ubscribed ackages
    refined_tasks = refine_tasks(tasks, config)

    print(" - Found {} valid {} bug's task{}".format(
        len(refined_tasks), "s" if len(refined_tasks) > 1 else "",
        config.tag)
    )

    # Create a set of all active Jira issues
    print("Retrieving all the imported LP Tasks in Jira")
    all_issues = find_bugs_in_jira_project(config.jira, config.project)
    print(" - Found {} issue{} in JIRA".format(
        len(all_issues), "s" if len(all_issues) > 1 else "")
    )

    process_issues(refined_tasks, all_issues, config)

# =============================================================================
