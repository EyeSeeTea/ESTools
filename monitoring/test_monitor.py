import monitor


def test_save_load_status():
    status = {'machine1': 0,
              'machine2': 1,
              'machine3': 2}
    monitor.save_status(status)
    assert monitor.load_last_status() == status


def test_get_status():
    assert monitor.get_status('localhost') == 0
    assert monitor.get_status('nonexistent_machine') == 2
    if monitor.dead:
        assert monitor.get_status(monitor.dead[0]) == 1


def test_associate():
    assert (monitor.associate(lambda x: x*x, range(10)) ==
            {x: x*x for x in range(10)})
