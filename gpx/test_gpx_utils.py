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
    assert gpx_utils.get_name({
        'id': 1234,
        'tags': {}
    }) == u'1234', 'Wrong name from ID'
