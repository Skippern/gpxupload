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
    u'Antigua and Barbuda': Rule('country'),
    u'Argentina': Rule('linear', levels=[4, 5, 6, 7]),
    u'Barbados': Rule('linear', levels=[6], accept=2),
    u'Belize': Rule('linear', levels=[4]),
    u'Bermuda': Rule('linear', levels=[6]),
    u'Bolivia': Rule('linear', levels=[4, 6, 8]),
    u'Brazil': Rule('linear', levels=[4, 8]),
    u'British Virgin Islands': Rule('country'),
    u'Canada': Rule('tree', tree={ 4: {
                    u'Alberta': {6: True, 8: True},
                    u'Manitoba': {6: True, 8: True},
                    u'Ontario': {6: True, 8: True},
                    u'British Columbia': { 6: { 8: True }},
                    u'New Brunswick': {6: { 8: True }},
                    u'Prince Edwuard Island': {6: {8: True }},
                    u'Saskatschewan': {6: {8: True }},
                    u'Nova Scotia': {5: {5: True, 6: {8: True}}},
                    u'New Foundland and Labrador': {8: True},
                    u'Nunavat': {8: True},
                    }}),
    u'Cayman Islands': Rule('country'),
    u'Chile': Rule('linear', levels=[4, 6, 8]),
    u'Colombia': Rule('tree', tree={4: { u'Bogota': True, 6: True}}),
    u'Comoros': Rule('linear', levels=[4]),
    u'Costa Rica': Rule('tree', tree={4: {6: True, 8: True}}),
    u'Cuba': Rule('linear', levels=[4, 6]),
    u'Dominica': Rule('linear', levels=[4]),
    u'Dominican Republic': Rule('linear', levels=[4, 6], accept=4),
    u'Ecuador': Rule('linear', levels=[4, 6]),
    u'El Salvador': Rule('tree', tree={4: True, 5: True, 6: True, 7: True}),
    u'Falkland Islands': Rule('country'),
    u'Greenland': Rule('country'),
    u'Grenada': Rule('country'),
    u'Guatamala': Rule('linear', levels=[4, 6]),
    u'Guyana': Rule('country'),
    u'Haiti': Rule('linear', levels=[4, 5, 8]),
    u'Honduras': Rule('linear', levels=[4, 6]),
    u'Jamaica': Rule('linear', levels=[5, 6]),
    u'Mexico': Rule('linear', levels=[4, 6]),
    u'Nicaragua': Rule('linear', levels=[4, 6]),
    u'Panama': Rule('linear', levels=[4]),
    u'Paraguay': Rule('linear', levels=[4, 8]),
    u'Peru': Rule('linear', levels=[4, 6, 8]),
    u'Saint Helena, Ascension and Tristan da Cunha': Rule('linear', levels=[3, 4], accept=3),
    u'Saint Kitts and Nevis': Rule('linear', levels=[10], accept=2),
    u'Saint Lucia': Rule('country'),
    u'Saint Vincent and the Grenadines': Rule('linear', levels=[6]),
    u'South Georgia and the South Sandwich Islands': Rule('linear', levels=[3]),
    u'Suriname': Rule('linear', levels=[4]),
    u'The Bahamas': Rule('linear', levels=[8]),
    u'Trinidad and Tobago': Rule('country'),
    u'Turks and Caicos Islands': Rule('linear', levels=[6]),
    u'United States of America': Rule('tree',
                                      tree={ 3: True, 4: {
                                      u'District of Colombia': {8: True},
                                      u'Connecticut': {6: True, 8: True},
                                      5: {5: True, 6: True, 8: True},
                                      }}),
    u'Uruguay': Rule('linear', levels=[4, 6]),
    u'Venezuela': Rule('linear', levels=[4, 6]),

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
    u'Bosnia and Herzegovina': Rule('tree', tree={4: {u'Brcko district of Bosnia and Herzegovina': True, u'Republika Srpska': {7: True}, 5: {6: True, 7: True}}}),
    u'British Sovereign Base Areas': Rule('country'),
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
    u'Greece': Rule('tree', tree={3: True, 4: {6: {7: True}}}),
    u'Guernsey': Rule('linear', levels=[4]),
    u'Hungary': Rule('linear', levels=[4, 5, 6, 7, 8]),
    u'Iceland': Rule('linear', levels=[5, 6]),
    u'Ireland': Rule('linear', levels=[5, 6, 7]),
    u'Isle of Man': Rule('linear', levels=[6, 8]),
    u'Italy': Rule('tree', tree={3: True, 4: {5: {6: {8: True}}}}),
    u'Jersey': Rule('country'),
    u'Kosovo': Rule('linear', levels=[4]),
    u'Latvia': Rule('linear', levels=[4, 6]),
    u'Liechtenstein': Rule('linear', levels=[6]),
    u'Lithuania': Rule('tree', tree={4: {5: {8: True}, 6: True}}),
    u'Luxembourg': Rule('linear', levels=[6]),
    u'Macedonia': Rule('tree', tree={4: { 6: True, 8: True}}),
    u'Malta': Rule('tree', tree={3: True, 4: {8: True}}),
    u'Moldova': Rule('tree', tree={4: {4: True, 6: { 6: True, 8: True}}}),
    u'Monaco': Rule('linear', levels=[8, 10]),
    u'Montenegro': Rule('linear', levels=[6]),
    u'Norway': Rule('linear', levels=[4, 7]),
    u'Portugal': Rule('linear', levels=[4, 7]),
    u'Poland': Rule('tree', tree={4: {6: {7: True, 8: True}}}),
    u'Romania': Rule('tree', tree={4: {6: True, 7: True}}),
    u'Russian Federation': Rule('tree', tree={3: {4: {5: True, 6: True}}}),
    u'San Marino': Rule('linear', levels=[8]),
    u'Serbia': Rule('tree', tree={4: {6: {7: True, 8: True}}}),
    u'Slovakia': Rule('tree', tree={3: True, 4: {6: True, 6: {8: True}}}),
    u'Slovenia': Rule('linear', levels=[5, 8]),
    u'Spain': Rule('tree', tree={4: {6: {7: True, 8: True}}}),
    u'Sweden': Rule('linear', levels=[3, 4, 7]),
    u'Switzerland': Rule('linear', levels=[4, 6, 8]),
                    u'The Netherlands': Rule('tree', tree={3: { u'Aruba': { 8: True }, u'Netherlands': { 4: { 8: True }} }}),
    u'Ukraine': Rule('linear', levels=[4, 6]),
    u'United Kingdom': Rule('tree', tree={4: {u'Northern Ireland': {10: True}, ## TODO historic admin_level 5 + 6
                  u'England': {5: {6: True, 8: True}}, 6: True}}),
    u'Vatican City': Rule('country'),

    ##############################
    #     Sub-Saharan Africa     #
    ##############################
    u'Angola': Rule('linear', levels=[4]),
    u'Benin': Rule('linear', levels=[4, 6]),
    u'Botswana': Rule('linear', levels=[4]),
    u'Burkina Faso': Rule('linear', levels=[4, 5, 6], accept=5),
    u'Cameroon': Rule('linear', levels=[4, 6, 8]),
    u'Cape Verde': Rule('linear', levels=[6]),
    u'Central African Republic': Rule('linear', levels=[4]),
    u'Chad': Rule('linear', levels=[4]),
    u'Congo-Brazzaville': Rule('linear', levels=[4, 6], accept=4),
    u'Congo-Kinshasa': Rule('tree', tree={4: {5: {6: True, 7: True}}}),
    u"Côte d'Ivoire": Rule('tree', tree={4: {5: True, 7: True, 8: True}}),
    u'Equatorial Guinea': Rule('linear', levels=[3, 4]),
    u'Gabon': Rule('linear', levels=[4, 6]),
    u'Gambia': Rule('linear', levels=[4]),
    u'Ghana': Rule('linear', levels=[4, 6]),
    u'Guinea': Rule('linear', levels=[4, 6, 8], accept=4),
    u'Guinnea-Bissau': Rule('linear', levels=[3, 4, 6], accept=3),
    u'Kenya': Rule('linear', levels=[4]),
    u'Lesotho': Rule('linear', levels=[5]),
    u'Liberia': Rule('linear', levels=[4, 6]),
    u'Madagascar': Rule('tree', tree={3: { u"Province d'Antanarivo": {8: True}, 4: {8: True}, 6: {9: True}}}),
    u'Malawi': Rule('linear', levels=[3, 6], accept=3),
    u'Mali': Rule('linear', levels=[4, 6]),
    u'Mauritania': Rule('linear', levels=[4]),
    u'Mauritius': Rule('tree', tree={3: {5: True}, 4: True}),
    u'Montserrat': Rule('linear', levels=[6]),
    u'Mozambique': Rule('tree', tree={4: {6: True, 8: True}}),
    u'Namibia': Rule('linear', levels=[4]),
    u'Niger': Rule('linear', levels=[4, 6], accept=4),
    u'Nigeria': Rule('linear', levels=[4, 6]),
    u'Rwanda': Rule('linear', levels=[4, 6, 8], accept=6),
    u'São Tomé and Príncipe': Rule('linear', levels=[4, 6], accept=4),
    u'Senegal': Rule('tree', tree={3: {6: True}, 7: {7: True, 8: True}}),
    u'Seychelles': Rule('country'),
    u'Sierra Leone': Rule('linear', levels=[4, 5, 6], accept=5),
    u'South Africa': Rule('linear', levels=[4, 6, 8]),
    u'South Sudan': Rule('linear', levels=[4, 5], accept=4),
    u'Swaziland': Rule('linear', levels=[4, 6]),
    u'Tanzania': Rule('linear', levels=[3, 4, 5], accept=4),
    u'Togo': Rule('tree', tree={4: {6: True, 9: True}}),
    u'Uganda': Rule('linear', levels=[3, 4]),
    u'Zambia': Rule('linear', levels=[4]),
    u'Zimbabwe': Rule('linear', levels=[4, 6]),

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
    u'Algeria': Rule('linear', levels=[4, 6, 7]),
    u'Bahrain': Rule('linear', levels=[4]),
    u'Djibouti': Rule('linear', levels=[4, 6], accept=4),
    u'Egypt': Rule('linear', levels=[4]),
    u'Eritrea': Rule('linear', levels=[4]),
    u'Ethiopia': Rule('linear', levels=[4, 5], accept=4),
    u'Iran': Rule('tree', tree={4: {5: {7: True}}, 8: True}),
    u'Iraq': Rule('linear', levels=[4]),
    u'Israel': Rule('linear', levels=[4, 8]),
    u'Jordan': Rule('linear', levels=[4]),
    u'Kuwait': Rule('linear', levels=[4]),
    u'Lebanon': Rule('linear', levels=[3, 4], accept=3),
    u'Libya': Rule('linear', levels=[4]),
    u'Morocco': Rule('tree', tree={4: True, 5: {6: True}}),
    u'Oman': Rule('linear', levels=[4]),
    u'Palestinian Territories': Rule('tree', tree={3: {5: True}, 9: True }),
    u'Qatar': Rule('linear', levels=[4]),
    u'Sharawi Arab Democratic Republic': Rule('country'),
    u'Saudi Arabia': Rule('linear', levels=[4]),
    u'Somalia': Rule('tree', tree={3: { 3: True, 4: {6: True}}}),
    u'Sudan': Rule('linear', levels=[4, 8], accept=4),
    u'Syria': Rule('linear', levels=[4]),
    u'Turkey': Rule('linear', levels=[3, 4, 6]),
    u'Tunisia': Rule('linear', levels=[8]),
    u'United Arab Emirates': Rule('linear', levels=[4]),
    u'Yemen': Rule('linear', levels=[4]),

    ##############################
    #            Asia            #
    ##############################
    u'Afghanistan': Rule('linear', levels=[4, 6]),
    u'Bangladesh': Rule('tree', tree={4: {5: True, 6: True, 8: True, 9: True}}),
    u'Bhutan': Rule('tree', tree={3: True, 4: True}),
    u'British Indian Ocean Territory': Rule('country'),
    u'Brunei': Rule('linear', levels=[6]),
    u'Burundi': Rule('linear', levels=[4, 6]),
    u'Cambodia': Rule('linear', levels=[4]),
    u'China': Rule('tree', tree={ 3: { u'Hong Kong': { 5: { 5: True, 6: True}}, u'Macao': { 5: True, 6: True }, 4: { 5: {5: True, 6: True}}}}),
    u'East Timor': Rule('linear', levels=[4]),
    u'India': Rule('tree', tree={3: True, 4: { 5: { 6: True, 8: True}}}),
    u'Indonesia': Rule('tree', tree={4: {5: True, 6: True, 7: True, 8: True}}),
    u'Japan': Rule('linear', levels=[4, 7]),
    u'Kazakhstan': Rule('linear', levels=[4, 6]),
    u'Kyrgystan': Rule('linear', levels=[4, 6]),
    u'Laos': Rule('linear', levels=[4, 6]),
    u'Malaysia': Rule('linear', levels=[4, 6], accept=4),
    u'Maldives': Rule('linear', levels=[4]),
    u'Mongolia': Rule('linear', levels=[4]),
    u'Myanmar': Rule('tree', tree={ 4: {5: True, 6: True, 7: True, 8: True}, }),
    u'Nepal': Rule('linear', levels=[4, 5, 6, 8]),
    u'North Korea': Rule('tree', tree={4: True, 6: True, 8: True}),
    u'Pakistan': Rule('tree', tree={4: {6: True, 8: True}}),
    u'Philippines': Rule('tree', tree={3: { u'Metro Manila': {6: True}, 4: {4: True, 6: True, 7: True}}}),
    u'Singapore': Rule('linear', levels=[6]),
    u'South Korea': Rule('linear', levels=[4, 6, 8], accept=6),
    u'Sri Lanka': Rule('tree', tree={4: {5: {6: {7: True}}, 8: True}}),
    u'Taiwan': Rule('tree', tree={5: True, 6: {8: True}}),
    u'Tajikistan': Rule('linear', levels=[4, 6]),
    u'Thailand': Rule('linear', levels=[4, 6], accept=4),
    u'Turkmenistan': Rule('linear', levels=[8]),
    u'Uzbekistan': Rule('tree', tree={4: {4: True, 6: True, 8: True}}),
    u'Vietnam': Rule('linear', levels=[4]),

    ##############################
    #    Australia & Oceania     #
    ##############################
    u'Australia': Rule('tree', tree={4: {
                       u'Victoria': {5: {6: {7: True}}},
                       u'Tasmania': {6: True},
                       u'Northern Territory': {6: True},
                       u'New South Wales': {6: True},
                       u'Australian Capital Territory': {7: True}}}),
    u'Cook Islands': Rule('linear', levels=[8]),
    u'Federated States of Micronesia': Rule('linear', levels=[4, 8]),
    u'Fiji': Rule('linear', levels=[4]),
    u'Kiribati': Rule('linear', levels=[8]),
    u'Marshall Islands': Rule('linear', levels=[8]),
    u'Nauru': Rule('country'),
    u'New Zealand': Rule('linear', levels=[4, 6], accept=4),
    u'Niue': Rule('linear', levels=[4]),
    u'Palau': Rule('linear', levels=[8]),
    u'Papua New Guinea': Rule('linear', levels=[3, 4]),
    u'Pitcairn Islands': Rule('country'),
    u'Samoa': Rule('country'),
    u'Solomon Islands': Rule('linear', levels=[4]),
    u'Tonga': Rule('treet', tree={3: {5: True, 7: True}, 4: { 4: True, 5: True}}),
    u'Tokelau': Rule('country'),
    u'Tuvalu': Rule('linear', levels=[8]),
    u'Vanuaty': Rule('linear', levels=[4]),
}),


def __get_resolver(obj_id, obj_name):
    """
    :param int obj_id: Object ID to test
    :param unicode obj_name: Object name to test
    :return GpxResolver: the resolver instance to use.
    """
    if obj_name in __NAME_RULES.keys():
        return __NAME_RULES[obj_name].create(obj_id, obj_name)
    elif obj_name is None:
        __LOG.error(u'Null country name: %s' % obj_id)
        return gpx_resolver.GpxResolver(obj_id, u'Unknown')
    else:
        __LOG.error(u'No rule for country: %s / %s, matching country only' % (obj_id, obj_name))
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
