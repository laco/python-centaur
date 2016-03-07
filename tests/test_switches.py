from centaur.switches import SwitchBoard, SwitchStates, PersistentSwitchBoard, InMemorySwitchManager


def test_create_empty_switchboard():
    board = SwitchBoard()
    assert board is not None
    assert board.is_enabled('MISSING_FEATURE_DEFAULTS_TO_FALSE') is False


def test_switchboard_with_test_switch():
    board = SwitchBoard()
    board.add_switch('TEST_SWITCH',
                     description='This is the description',
                     state=SwitchStates.GLOBAL_ENABLED)
    board.add_switch('DISABLED_SWITCH',
                     state=SwitchStates.GLOBAL_DISABLED)
    assert board.is_enabled('TEST_SWITCH') is True
    assert board.is_enabled('DISABLED_SWITCH') is False


def test_switchboard_all_switches():
    board = SwitchBoard()
    board.add_switch('ENABLED_TEST1', state=SwitchStates.GLOBAL_ENABLED)
    board.add_switch('DISABLED_TEST2')

    assert board.get_context() == {'ENABLED_TEST1': True, 'DISABLED_TEST2': False}
    assert board.get_context(overwrite={'DISABLED_TEST2': True}) == {'ENABLED_TEST1': True, 'DISABLED_TEST2': True}


def test_inmemory_persistent_switches():
    manager = InMemorySwitchManager({
        'TEST1': {'name': 'TEST1', 'state': SwitchStates.GLOBAL_ENABLED}
    })
    board = PersistentSwitchBoard(manager=manager)
    board.add_switch('TEST2')
    assert board.is_enabled('TEST1') is True
    assert 'TEST2' in manager.state
    assert manager.state['TEST2']['state'] == SwitchStates.GLOBAL_DISABLED


def test_selective_switch_with_conditions():
    board = SwitchBoard()
    board.add_switch('TEST_SWITCH',
                     state=SwitchStates.SELECTIVE,
                     conditions=('in', 'ipaddress', ['127.0.0.1', '192.168.0.1']))
    assert board.is_enabled('TEST_SWITCH') is False
    assert board.is_enabled('TEST_SWITCH', ipaddress='127.0.0.1') is True
    assert board.is_enabled('TEST_SWITCH', ipaddress='192.168.0.1') is True
    assert board.is_enabled('TEST_SWITCH', ipaddress='8.8.4.4') is False


def test_selective_switch_without_conditions_always_false():
    board = SwitchBoard()
    board.add_switch('TEST_SWITCH',
                     state=SwitchStates.SELECTIVE)
    assert board.is_enabled('TEST_SWITCH') is False
    assert board.is_enabled('TEST_SWITCH', ipaddress='127.0.0.1') is False
