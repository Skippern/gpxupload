import gpx_utils


def test_get_name():
    assert gpx_utils.get_name({
        'id': 1234,
        'tags': {
            'name': u'El Nomo',
            'name:en': u'The Name'
        }
    }) == u'The Name', 'Wrong name from english-name'
    assert gpx_utils.get_name({
        'id': 1234,
        'tags': {
            'name': u'El Nomo',
            'name:no': u'Navnet'
        }
    }) == u'El Nomo', 'Wrong name from local-name'
    try:
        gpx_utils.get_name({
            'id': 1234,
            'tags': {}
        })
        assert False, 'No exception'
    except KeyError as e:
        assert e.message == 'name', 'Key "name" was not the failure.'
