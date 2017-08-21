#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import gpx_resolver

__LOG = logging.getLogger('gpx_rules')


class Rule(object):
    def __init__(self, rule_type, **kwargs):
        """
        :param str rule_type: The rule type.
        :param **kwargs: KW args for the resolver.
        """
        self.rule_type = str(rule_type)
        self.kwargs = kwargs

    def create(self, obj_id, obj_name):
        """
        :param int obj_id: The object ID for the country.
        :param unicode obj_name: The country name
        :return gpx_resolver.GpxResolver: The resolver to use.
        """
        if self.rule_type is 'linear':
            return gpx_resolver.LinearResolver(obj_id, obj_name, **self.kwargs)
        elif self.rule_type is 'tree':
            return gpx_resolver.TreeResolver(obj_id, obj_name, **self.kwargs)
        elif self.rule_type is 'country':
            return gpx_resolver.CountryResolver(obj_id, obj_name)
        raise Exception(u'Unknown rule type for country %s: %s' % (obj_name, self.rule_type))


# Keep rules in their respective continental group, and
# alphabetical within the group.
__NAME_RULES = dict({
    ##############################
    #          Americas          #
    ##############################
    u'Anguilla': Rule('country'),
    u'Brazil': Rule('linear', levels=[4, 8]),

    ##############################
    #           Europe           #
    ##############################
    u'Albania': Rule('linear', levels=[6, 7, 8]),
    u'Andorra': Rule('linear', levels=[7]),
    u'Armenia': Rule('linear', levels=[4]),
    u'Austria': Rule('linear', levels=[4, 6, 8], accept=4),
    u'Azerbaijan': Rule('linear', levels=[4]),
    u'Belarus': Rule('linear', levels=[4, 6]),
    u'Belgium': Rule('tree', tree={4: {6: True, 7: {8: True}}}),
    u'Bosnia and Herzegovina': Rule(
        'tree',
        tree={4: {u'Brcko district of Bosnia and Herzegovina': True,
                  u'Republika Srpska': {7: True},
                  5: {6: True, 7: True}}}),
    u'Bulgaria': Rule('linear', levels=[6, 8]),
    u'Croatia': Rule('tree', tree={6: {6: True, 7: True, 8: True}}),
    u'Cyprus': Rule('tree', tree={6: {6: True, 7: True, 8: True}}),
    u'Czech Republic': Rule('linear', levels=[4, 6, 7, 8]),
    u'Denmark': Rule('tree', tree={4: True, 7: True}),
    u'Estonia': Rule('linear', levels=[6, 8]),
    u'Faroe Islands': Rule('linear', levels=[4, 8]),
    u'Finland': Rule('linear', levels=[4, 6, 8]),
    u'France': Rule('linear', levels=[4, 6, 8]),
    u'Georgia': Rule('tree', tree={3: {3: True, 6: {6: True, 8: True}},
                                   4: {4: True, 6: {6: True, 8: True}}}),
    u'Germany': Rule(
        'tree',
        tree={4: {u'Berlin': True,
                  u'Hamburg': {4: True, 8: True},
                  u'Baden-Württemberg': {5: {6: True}},
                  u'Free State of Bavaria': {5: {6: True}},
                  u'North Rhine-Westphalia': {5: {6: True}},
                  6: True}}),
    u'Gibraltar': Rule('linear', levels=[4], accept=2),
    # --- ETC ---

    u'Norway': Rule('linear', levels=[4, 7]),

    ##############################
    #     Sub-Saharan Africa     #
    ##############################

    ##############################
    # North-Africa & Middle East #
    ##############################
    #
    # I know this is the least defined
    # region of all times... But puts
    # in a region between Europe,
    # Asia and Sub-Saharan Africa,
    # each with a similar magnitude of
    # countries to check.
    #
    # Middle east includes Turkey,
    #   Iran, Arabian Peninsula and
    #   North Africa.
    # Causcasus & Russia -> Europe
    # Central Asia (*Stan) -> Asia
    # South Asia (Pakistan, India,
    #   Bangladesh, Sri Lanka -> Asia
    # Mauritania -> Sub-Saharan Africa
    # South-Sudan -> Sub-Saharan Africa
    u'Bahrain': Rule('linear', levels=[4]),
    u'Kuwait': Rule('linear', levels=[4]),

    ##############################
    #            Asia            #
    ##############################

    ##############################
    #    Australia & Oceania     #
    ##############################
})


def __get_resolver(obj_id, obj_name):
    """
    :param int obj_id: Object ID to test
    :param unicode obj_name: Object name to test
    :return GpxResolver: the resolver instance to use.
    """
    if obj_name in __NAME_RULES.keys():
        return __NAME_RULES[obj_name].create(obj_id, obj_name)
    elif obj_name is None:
        __LOG.warn(u'Null country name: %s' % obj_id)
        return gpx_resolver.GpxResolver(obj_id, u'Unknown')
    else:
        __LOG.warn(u'No rule for country: %s / %s, matching country only' % (obj_id, obj_name))
        return gpx_resolver.CountryResolver(obj_id, obj_name)


def test_country(track, country_obj_id, country_name):
    """
    Test the track against the country object (polygon) with given name.
    :param track: The track to test.
    :param country_obj_id: The object ID of the country.
    :param country_name: The name of the country.
    :return bool, []: True if the test passed, and list of tags.
    """
    return __get_resolver(country_obj_id, country_name).test(track)
