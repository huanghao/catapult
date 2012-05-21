import os


def test_dummy():
    home = '/tmp/dummy'

    assert 0 == os.system("fab proj:dummy exterminate")
    assert not os.path.exists(home)

    assert 0 == os.system("fab proj:dummy setup:v1.1")
    current = os.path.join(home, 'current')
    v1 = os.readlink(current)

    assert 0 == os.system("fab proj:dummy ideploy:v1.2")
    v2 = os.readlink(current)
    assert v1 != v2

    assert 0 == os.system("fab proj:dummy rollback")
    assert v1 == os.readlink(current)

    assert 0 == os.system("fab proj:dummy exterminate")
    assert not os.path.exists(home)


def test_yummy():
    home = '/tmp/yummy'

    assert 0 == os.system("fab proj:yummy exterminate")
    assert not os.path.exists(home)

    assert 0 == os.system("fab proj:yummy setup:v1.1")
    current = os.path.join(home, 'current')
    v1 = os.readlink(current)

    assert 0 == os.system("fab proj:yummy deploy:v1.2")
    v2 = os.readlink(current)
    assert v1 != v2

    assert 0 == os.system("fab proj:yummy rollback")
    assert v1 == os.readlink(current)

    assert 0 == os.system("fab proj:yummy exterminate")
    assert not os.path.exists(home)


def main():
    dirname = os.path.dirname(os.path.abspath(__file__))
    catapult_dir = os.path.join(dirname, '..')
    os.chdir(catapult_dir)
    test_dummy()
    #test_yummy() #FIXME:git repo for testing does not checkin


if __name__ == '__main__':
    main()
