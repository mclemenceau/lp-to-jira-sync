from unittest.mock import patch, MagicMock
from lp_to_jira_sync.sync_config import SyncConfig


@patch('lp_to_jira_sync.sync_config.Launchpad')
@patch('lp_to_jira_sync.sync_config.jira_config')
def test_init_with_jira_and_lp(mock_launchpad, mock_jira_config):
    mock_jira = MagicMock()
    mock_jira_config.return_value = MagicMock(jira=mock_jira)

    mock_lp = MagicMock()
    mock_launchpad.login_with.return_value = mock_lp

    config = SyncConfig(jira=mock_jira, lp_api=mock_lp, project='TEST_PROJECT')

    assert config.jira == mock_jira
    assert config.project == 'TEST_PROJECT'
    assert config.lp == mock_lp
    assert config.tag == ''
    assert config.team == ''
    assert config.restricted_pkgs == []
    assert config.special_packages == []
    assert config.dry_run is True
    assert config.args is None


@patch('lp_to_jira_sync.sync_config.Launchpad')
@patch('lp_to_jira_sync.sync_config.jira_config')
@patch('lp_to_jira_sync.sync_config.JIRA')
def test_init_with_jira_config(mock_jira, mock_jira_config, mock_launchpad):
    # Create a mock Jira Config
    mock_jira_config_instance = MagicMock()
    # Set the return value of the mocked jira_config function
    mock_jira_config.return_value = MagicMock(jira=mock_jira_config_instance)

    # Create a mock Jira instance
    mock_jira_instance = MagicMock()

    # Set the return value of the mocked jira_config function
    mock_jira.return_value = mock_jira_instance

    mock_lp = MagicMock()
    mock_launchpad.login_with.return_value = mock_lp

    # Create a SyncConfig instance
    config = SyncConfig(project='TEST_PROJECT')

    # Verify the attributes of the SyncConfig instance
    assert config.jira == mock_jira_instance
    assert config.project == 'TEST_PROJECT'
    assert config.lp is not None
    assert config.tag == ''
    assert config.team == ''
    assert config.restricted_pkgs == []
    assert config.special_packages == []
    assert config.dry_run is True
    assert config.args is None


@patch('lp_to_jira_sync.sync_config.requests')
@patch('lp_to_jira_sync.sync_config.jira_config')
@patch('lp_to_jira_sync.sync_config.Launchpad')
def test_init_with_lp_team(mock_launchpad, mock_jira_config, mock_requests):
    mock_jira = MagicMock()
    mock_jira_config.return_value = MagicMock(jira=mock_jira)

    mock_lp = MagicMock()
    mock_launchpad.login_with.return_value = mock_lp

    pkg1 = MagicMock()
    pkg1.configure_mock(name='pkg1')

    pkg2 = MagicMock()
    pkg2.configure_mock(name='pkg2')

    (mock_lp.people.__getitem__.return_value
        .getBugSubscriberPackages.return_value) = [pkg1, pkg2]

    # We will skip the json download at this time
    mock_requests = MagicMock()
    mock_requests.get.return_value = 404

    config = SyncConfig(jira=mock_jira,
                        lp_api=mock_lp,
                        project='TEST_PROJECT',
                        lp_team='test_team')

    assert config.jira == mock_jira
    assert config.project == 'TEST_PROJECT'
    assert config.lp == mock_lp
    assert config.tag == ''
    assert config.team == 'test_team'
    assert config.restricted_pkgs == ['pkg1', 'pkg2']
    assert config.special_packages == []
    assert config.dry_run is True
    assert config.args is None

