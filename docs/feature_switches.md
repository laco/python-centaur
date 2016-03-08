# Feature Switches

## Deal with switches

Define a SwitchBoard:



```py
from centaur.switches import SwitchBoard, SwitchStates


board = SwitchBoard()
board.add_switch('TEST_SWITCH',
                 description='This is the description',
                 state=SwitchStates.GLOBAL_ENABLED)
board.add_switch('DISABLED_SWITCH',
                 state=SwitchStates.GLOBAL_DISABLED)
```

Check for individual switches:

```py
assert board.is_enabled('TEST_SWITCH') is True
assert board.is_enabled('DISABLED_SWITCH') is False

```

## Enabled, Disabled and Selective Switches

## Persistent SwitchBoards