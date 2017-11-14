import gpx_utils


def test_get_name():
    assert gpx_utils.get_name({
        'name': u'El Nome',
        'name:en': u'The Name'
    }) == u'The Name', 'Wrong name from english-name'
    assert gpx_utils.get_name({
        'name': u'El Nome',
        'name:no': u'Navnet'
    }) == u'El Nome', 'Wrong name from local-name'
    try:
        gpx_utils.get_name({})
        assert False, 'No exception'
    except KeyError as e:
        assert e.message == 'name', 'Key "name" was not the failure.'
