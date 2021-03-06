#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import gpx_data
import gpx_utils


class GpxResolver(object):
    def __init__(self, obj_id, name):
        """
        :param int obj_id: Object ID of the region (admin level 2)
        :param unicode name: The name of the region (country name).
        """
        self._LOG = logging.getLogger('resolver.%s' % self.__class__.__name__)
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
        :param int obj_id: Object ID of the region (admin level 2)
        :param unicode name: The name of the region (country name).
        """
        super(CountryResolver, self).__init__(obj_id, name)

    def test(self, track):
        """
        Tests track against the resolver instance.

        :param track: The track to test the region against.
        :return (bool, []): If the resolution did find / match the region, and a list of tags
                            associated with that region.
        """
        country = gpx_data.load_geo_shape(self.id, 2, self.name)
        if gpx_utils.test_object(track, country):
            return True, gpx_utils.get_tags(gpx_data.load_tags(self.id, 2))
        return False, []


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
        :param int obj_id: Object ID of the region (admin level 2)
        :param unicode name: The name of the region (country name).
        :param [] levels: The levels to test in the region.
        """
        super(LinearResolver, self).__init__(obj_id, name)
        if levels is None:
            raise Exception(u'Invalid rule, no levels to check for %s', name)

        self.levels = levels
        if accept is 0:
            accept = levels[-1]
        elif accept is not 2 and accept not in levels:
            raise Exception(u'Invalid rule, accept level (%s) not in test-levels %s: %s' %
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

        relations = gpx_data.load_relations(obj_id, obj_level, next_level)
        for rel in relations:
            rel_id = int(rel['id'])
            rel_level = int(rel['tags']['admin_level'])
            rel_name = gpx_utils.get_name(rel['tags'])

            if rel_level is not next_level:
                raise AssertionError(u"Relation level mismatch: %s != %s for %s" % (rel_level, next_level, rel_name))

            region = gpx_data.load_geo_shape(rel_id, rel_level, rel_name)
            if region is None:
                raise AssertionError(u"Loaded None region for: %s" % rel_name)

            if gpx_utils.test_object(track, region):
                r_tags = gpx_data.load_tags(rel_id, rel_level)
                tags.extend(gpx_utils.get_tags(r_tags))
                reg_accept, reg_tags = self.__test_recursive(track, rel_id, rel_level, recurse_levels)
                if reg_accept:
                    accepted = True
                    tags.extend(reg_tags)

                if not accepted:
                    raise AssertionError(u'Region matched, but not accepted: (%s/%s) %s' %
                                         (rel_level, rel_id, rel_name))
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
        accepted = False
        tags = []
        country = gpx_data.load_geo_shape(self.id, 2, self.name)
        if gpx_utils.test_object(track, country):
            c_tags = gpx_data.load_tags(self.id, 2)
            tags.extend(gpx_utils.get_tags(c_tags))
            accepted, rel_tags = self.__test_recursive(track, self.id, 2, self.levels)
            if accepted:
                tags.extend(rel_tags)
            else:
                raise AssertionError(u'Country matched but not accepted: %s, levels=%s' % (self.name, self.levels))
        return accepted, tags


class TreeResolver(GpxResolver):
    def __init__(self, obj_id, name, tree):
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

        :param int obj_id: Object ID of the region (admin level 2)
        :param unicode name: The name of the region (country name).
        :param dict tree: The rule tree.
        """
        super(TreeResolver, self).__init__(obj_id, name)
        if tree is None:
            raise AssertionError(u'TreeRule for %s (%s) has no tree' % (name, obj_id))
        self.tree = tree

    def __test_recursive(self, track, region, tree, region_id, region_level, name):
        """
        This object has already matched the region.

        :param track: The track to test.
        :param region: The rules to test.
        :param bool|dict tree: The rules for handling the region.
        :param int region_id: The region ID to test.
        :param int region_level: The region level to test.
        :param unicode name: The region name.
        :return (bool, []): True if accepted and list of tags.
        """
        if not isinstance(tree, dict):
            if tree is True:
                return True, []
            raise Exception(u'Invalid rule: ' + repr(tree))

        # A name rule replaces the current rule.
        if name in tree.keys():
            return self.__test_recursive(track, region, tree[name], region_id, region_level, name)

        accepted = False
        tags = []
        for criteria_level, rule in tree.iteritems():
            if isinstance(criteria_level, int):
                if criteria_level is region_level:
                    # If the rule has the same admin level as the current region,
                    # then the rule MUST be 'True', and causes the region to be accepted
                    # even if no sub-region is matching.
                    if rule is True:
                        accepted = True
                    else:
                        raise AssertionError(u'Invalid self-level rule on level %s, must be True' % criteria_level)
                elif criteria_level > region_level:
                    relations = gpx_data.load_relations(region_id, region_level, criteria_level)
                    for rel in relations:
                        rel_id = int(rel['id'])
                        rel_level = int(rel['tags']['admin_level'])
                        rel_name = gpx_utils.get_name(rel['tags'])

                        if rel_level is not criteria_level:
                            raise AssertionError(u'Relation level is not same as checked criteria %s != %s' % (rel_level, criteria_level))

                        rel_ok, rel_tags = self.__test_tree_recursive(
                                track, rel_id, rel_level, tree[criteria_level], rel_name)
                        if rel_ok:
                            accepted = True
                            tags.extend(rel_tags)
                else:
                    raise AssertionError(u'Criteria level below region level (%s < %s)' %
                                         (criteria_level, region_level))

        return accepted, tags

    def __test_tree_recursive(self, track, obj_id, obj_level, tree, name):
        """
        :param track: The track to test.
        :param int obj_id: The object ID to test against.
        :param int obj_level: The administrative level of the object
        :param bool|dict tree: The rule tree
        :param unicode name: Name of the region to test
        :return (bool, []): True if accepted and list of tags.
        """
        accepted = False
        tags = []
        region = gpx_data.load_geo_shape(obj_id, obj_level, name)
        if gpx_utils.test_object(track, region):
            c_tags = gpx_data.load_tags(obj_id, obj_level)
            tags.extend(gpx_utils.get_tags(c_tags))
            # Do the actual test for the region.
            accepted, rel_tags = self.__test_recursive(track, region, tree, obj_id, obj_level, name)
            if accepted:
                tags.extend(rel_tags)
            else:
                if obj_level is 2:
                    raise AssertionError(u'Country %s matched but not accepted' % name)
                self._LOG.warn(u'Region matched, but not accepted: (%s/%s) %s' %
                               (obj_level, obj_id, name))
        return accepted, tags

    def test(self, track):
        """
        Tests track against the resolver instance.

        :param track: The track to test the region against.
        :return (bool, []): If the resolution did find / match the region, and a list of tags
                            associated with that region.
        """
        return self.__test_tree_recursive(track, self.id, 2, self.tree, self.name)
