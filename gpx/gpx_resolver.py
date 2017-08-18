#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import gpx_data
import gpx_loader
import gpx_utils

__LOG = logging.getLogger('gpx_resolver')


class GpxResolver(object):
    def __init__(self, obj_id, name):
        self.id = obj_id
        self.name = name
        pass

    def test(self, track):
        """
        Tests track against the resolver instance.

        :param track: The track to test the region against.
        :return (bool, []): If the resolution did find / match the region, and a list of tags
                            associated with that region.
        """
        return False, []


class CountryResolver(GpxResolver):
    """
    Basic resolver that resolves a country (level 2), and stops there.
    Will match as long as track tests against the country boundaries.
    """
    def __init__(self, obj_id, name):
        """
        :param obj_id: Object ID of the region (admin level 2)
        :param name: The name of the region (country name).
        """
        super(CountryResolver, self).__init__(obj_id, name)

    def test(self, track):
        """
        Tests track against the resolver instance.

        :param track: The track to test the region against.
        :return (bool, []): If the resolution did find / match the region, and a list of tags
                            associated with that region.
        """
        ok = False
        tags = []
        country = gpx_data.load_object(self.id, 2, self.name)
        if gpx_utils.test_object(track, country):
            tags.extend(gpx_data.get_tags(country['tags']))
        return ok, tags


class LinearResolver(GpxResolver):
    """
    Basic resolver that resolves a region / country with a simple N layered
    admin level setup. Level 2 (country) is given, the other levels. It accept
    any regions that are the lowest admin level, and if the matching region
    admin-level is equal to the accept param.

    E.g.:

    levels=[4, 6]

    Searches for level 4, and if matching:
    - Searches level 6 within the region, and if matching accept.

    So all matches must have a valid level 6.

    levels=[4, 6], accept=4

    Searches for level 4, and if matching accepts and:
    - Searches level 6 within the region, and if matching accept.

    Both empty level 4 and also matching level 6 regions are accepted.
    """
    def __init__(self, obj_id, name, levels=None, accept=0):
        """
        :param obj_id: Object ID of the region (admin level 2)
        :param name: The name of the region (country name).
        :param levels: The levels to test in the region.
        """
        super(LinearResolver, self).__init__(obj_id, name)
        if levels is None:
            raise Exception("Invalid rule, no levels to check for %s", name)

        self.levels = levels
        if accept is 0:
            accept = levels[-1]
        elif accept is not 2 and accept not in levels:
            raise Exception("Invalid rule, accept level (%s) not in test-levels %s: %s" %
                            (accept, levels, name))
        self.accept = accept

    def __test_recursive(self, track, obj_id, obj_level, levels):
        accepted = False
        tags = []
        if len(levels) == 0:
            return True, tags
        if obj_level is self.accept:
            accepted = True

        next_level = levels[0]
        recurse_levels = levels[1:]

        relations = gpx_loader.get_relations_in_object(obj_level, obj_id)
        for rel in relations['elements']:
            try:
                rel_id = rel['id']
                rel_level = rel['tags']['admin_level']
                try:
                    rel_name = rel['tags']['name']
                except KeyError:
                    try:
                        rel_name = rel['tags']['name:en']
                    except KeyError:
                        rel_name = str(rel_id)
                rel_name = gpx_utils.enforce_unicode(rel_name)

                if rel_level is next_level:
                    region = gpx_data.load_object(rel_id, rel_level, rel_name)
                    if region is None:
                        continue

                    if gpx_utils.test_object(track, region):
                        if self.accept == rel_level:
                            accepted = True

                        tags.extend(gpx_data.get_tags(region['tags']))
                        reg_accept, reg_tags = self.__test_recursive(track, rel_id, rel_level, recurse_levels)
                        if reg_accept:
                            accepted = True
                            tags.extend(reg_tags)
            except KeyError:
                continue

        if not accepted:
            tags = []
        return accepted, tags

    def test(self, track):
        """
        Tests track against the resolver instance.

        :param track: The track to test the region against.
        :return (bool, []): If the resolution did find / match the region, and a list of tags
                            associated with that region.
        """
        ok = False
        tags = []
        country = gpx_data.load_object(self.id, 2, self.name)
        if gpx_utils.test_object(track, country):
            tags.extend(gpx_data.get_tags(country['tags']))
            ok, rel_tags = self.__test_recursive(track, self.id, 2)
            if ok:
                tags.extend(rel_tags)
        return ok, tags


class TreeResolver(GpxResolver):
    def __init__(self, obj_id, name, tree=None):
        """
        The rules are as follows. For each level checked, you have three
        types of criteria, which will be tested in order:
         - same-level : Accepted (but continue), rule must be 'True'.
         - unicode    : Recurse on rule if the current region matches and return (stop matching).
         - sub-level  : Recurse on sub-division matching admin level, (stop matching if accepted).

        For the rule, match the region, and if:
         - True, accept and return.
         - dict{criteria:rule}, recurse and test with the given rules.

        Example:

        tree = {3: True,
                4: {5: True}}

        - Search for level 3, and if found accept.
        - Search for level 4, abd if found:
           - Search for level 5, and if found accept.

        tree = {4: {u'Berlin': True,
                    u'Hamburg': {4: True, 8: True},
                    6: {8: True}}}

        - Search for level 4 and if found:
           - If region name is 'Berlin', accept.
           - Else if region name is 'Hamburg', accept and:
               - Search for level 8, and if found accept.
           - Else search for level 6, and if found:
               - Search for level 8, and if found accept.

        :param int obj_id: The country object ID.
        :param unicode name: The name of the country.
        :param dict tree: The rule tree.
        """
        super(TreeResolver, self).__init__(obj_id, name)
        if tree is None:
            raise Exception("TreeRule for %s (%s) has no tree" % (name, obj_id))
        self.tree = tree

    def test(self, track):
        """
        Tests track against the resolver instance.

        :param track: The track to test the region against.
        :return (bool, []): If the resolution did find / match the region, and a list of tags
                            associated with that region.
        """
        # TODO: Implement!
        return False, []
