import logging
import copy
import math
from enum import Enum
from cobra.core import Metabolite, Reaction
from cobra.core.dictlist import DictList
from cobra.util import format_long_string
from modelseedpy.core.msmodel import get_direction_from_constraints, \
    get_reaction_constraints_from_direction, get_cmp_token
from cobra.core.dictlist import DictList
#from cobrakbase.kbase_object_info import KBaseObjectInfo

logger = logging.getLogger(__name__)


class AttrDict(dict):
    """
    Base object to use for subobjects in KBase objects
    """
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class TemplateReactionType(Enum):
    CONDITIONAL = 'conditional'
    UNIVERSAL = 'universal'
    SPONTANEOUS = 'spontaneous'
    GAPFILLING = 'gapfilling'


class NewModelTemplateCompound:

    def __init__(self, cpd_id, formula=None, name='', default_charge=None,
                 mass=None, delta_g=None, delta_g_error=None, is_cofactor=False,
                 abbreviation='', aliases=None):
        self.id = cpd_id
        self.formula = formula
        self.name = name
        self.abbreviation = abbreviation
        self.default_charge = default_charge
        self.mass = mass
        self.delta_g = delta_g
        self.delta_g_error = delta_g_error
        self.is_cofactor = is_cofactor
        self.aliases = []
        if aliases:
            self.aliases = aliases
        self.species = set()
        self._template = None

    @staticmethod
    def from_dict(d):
        return NewModelTemplateCompound(
            d['id'], d['formula'], d['name'],
            d['defaultCharge'], d['mass'],
            d['deltaG'], d['deltaGErr'],
            d['isCofactor'] == 1,
            d['abbreviation'],
            d['aliases']
        )

    def get_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'abbreviation': self.abbreviation,
            'aliases': [],
            'defaultCharge': self.default_charge,
            'deltaG': self.delta_g,
            'deltaGErr': self.delta_g_error,
            'formula': self.formula,
            'isCofactor': 1 if self.is_cofactor else 0,
            'mass': self.mass
        }

    def __repr__(self):
        return "<%s %s at 0x%x>" % (self.__class__.__name__, self.id, id(self))

    def __str__(self):
        return "{}:{}".format(self.id, self.name)

    def _repr_html_(self):
        return """
        <table>
            <tr>
                <td><strong>Compound identifier</strong></td><td>{id}</td>
            </tr><tr>
                <td><strong>Name</strong></td><td>{name}</td>
            </tr><tr>
                <td><strong>Memory address</strong></td>
                <td>{address}</td>
            </tr><tr>
                <td><strong>Formula</strong></td><td>{formula}</td>
            </tr><tr>
                <td><strong>In {n_species} species</strong></td><td>
                    {species}</td>
            </tr>
        </table>""".format(id=self.id, name=format_long_string(self.name),
                           formula=self.formula,
                           address='0x0%x' % id(self),
                           n_species=len(self.species),
                           species=format_long_string(
                               ', '.join(r.id for r in self.species), 200))


class NewModelTemplateCompCompound(Metabolite):

    def __init__(self, comp_cpd_id, charge, compartment, cpd_id, max_uptake=0, template=None):
        self._template_compound = None
        super().__init__(comp_cpd_id, '', '', charge, compartment)
        self._template = template
        self.cpd_id = cpd_id
        self.max_uptake = max_uptake
        if self._template:
            if self.cpd_id in self._template.compounds:
                self._template_compound = self._template.compounds.get_by_id(self.cpd_id)

    @property
    def compound(self):
        return self._template_compound

    @property
    def name(self):
        if self._template_compound:
            return self._template_compound.name
        return ''

    @name.setter
    def name(self, value):
        if self._template_compound:
            self._template_compound.name = value

    @property
    def formula(self):
        if self._template_compound:
            return self._template_compound.formula
        return ''

    @formula.setter
    def formula(self, value):
        if self._template_compound:
            self._template_compound.formula = value

    @staticmethod
    def from_dict(d, template=None):
        return NewModelTemplateCompCompound(
            d['id'],
            d['charge'],
            d['templatecompartment_ref'].split('/')[-1],
            d['templatecompound_ref'].split('/')[-1],
            d['maxuptake'],
            template,
        )

    def get_data(self):
        return {
            'charge': self.charge,
            'id': self.id,
            'maxuptake': self.max_uptake,
            'templatecompartment_ref': '~/compartments/id/' + self.compartment,
            'templatecompound_ref': '~/compounds/id/' + self.cpd_id
        }


class NewModelTemplateReaction(Reaction):

    def __init__(self, rxn_id: str, reference_id: str, name='', subsystem='', lower_bound=0.0, upper_bound=None,
                 reaction_type=TemplateReactionType.CONDITIONAL, gapfill_direction='=',
                 base_cost=1000, reverse_penalty=1000, forward_penalty=1000,
                 status='OK', delta_g=0.0, delta_g_err=0.0, reference_reaction_id=None):
        """

        :param rxn_id:
        :param reference_id:
        :param name:
        :param subsystem:
        :param lower_bound:
        :param upper_bound:
        :param reaction_type:
        :param gapfill_direction:
        :param base_cost:
        :param reverse_penalty:
        :param forward_penalty:
        :param status:
        :param delta_g:
        :param delta_g_err:
        :param reference_reaction_id: DO NOT USE THIS duplicate of reference_id
        :param template:
        """
        super().__init__(rxn_id, name, subsystem, lower_bound, upper_bound)
        self.reference_id = reference_id
        self.GapfillDirection = gapfill_direction
        self.base_cost = base_cost
        self.reverse_penalty = reverse_penalty
        self.forward_penalty = forward_penalty
        self.status = status
        self.type = reaction_type.value if type(reaction_type) == TemplateReactionType else reaction_type
        self.deltaG = delta_g
        self.deltaGErr = delta_g_err
        self.reference_reaction_id = reference_reaction_id  #TODO: to be removed
        self.complexes = DictList()
        self.templateReactionReagents = {}
        self._template = None

    @property
    def gene_reaction_rule(self):
        return ' or '.join(map(lambda x: x.id, self.complexes))

    @gene_reaction_rule.setter
    def gene_reaction_rule(self, gpr):
        pass

    @property
    def compartment(self):
        """

        :return:
        """
        return get_cmp_token(self.compartments)

    @staticmethod
    def from_dict(d, template):
        metabolites = {}
        complexes = set()
        for o in d['templateReactionReagents']:
            comp_compound = template.compcompounds.get_by_id(o['templatecompcompound_ref'].split('/')[-1])
            metabolites[comp_compound] = o['coefficient']
        for o in d['templatecomplex_refs']:
            protein_complex = template.complexes.get_by_id(o.split('/')[-1])
            complexes.add(protein_complex)
        lower_bound, upper_bound = get_reaction_constraints_from_direction(d['direction'])
        if 'lower_bound' in d and 'upper_bound' in d:
            lower_bound = d['lower_bound']
            upper_bound = d['upper_bound']
        reaction = NewModelTemplateReaction(
            d['id'], d['reaction_ref'].split('/')[-1], d['name'], '', lower_bound, upper_bound,
            d['type'], d['GapfillDirection'],
            d['base_cost'], d['reverse_penalty'], d['forward_penalty'],
            d['status'] if 'status' in d else None,
            d['deltaG'] if 'deltaG' in d else None,
            d['deltaGErr'] if 'deltaGErr' in d else None,
            d['reaction_ref'].split('/')[-1]
        )
        reaction.add_metabolites(metabolites)
        reaction.add_complexes(complexes)
        return reaction

    def add_complexes(self, complex_list):
        self.complexes += complex_list

    @property
    def cstoichiometry(self):
        return dict(((met.id, met.compartment), coefficient) for (met, coefficient) in self.metabolites.items())

    def remove_role(self, role_id):
        pass

    def remove_complex(self, complex_id):
        pass

    def get_roles(self):
        """

        :return:
        """
        roles = set()
        for cpx in self.complexes:
            for role in cpx.roles:
                roles.add(role)
        return roles

    def get_complexes(self):
        return self.complexes

    def get_complex_roles(self):
        res = {}
        for complexes in self.data['templatecomplex_refs']:
            complex_id = complexes.split('/')[-1]
            res[complex_id] = set()
            if self._template:
                cpx = self._template.get_complex(complex_id)

                if cpx:
                    for complex_role in cpx['complexroles']:
                        role_id = complex_role['templaterole_ref'].split('/')[-1]
                        res[complex_id].add(role_id)
                else:
                    print('!!')
        return res

    def get_data(self):
        template_reaction_reagents = list(map(lambda x: {
            'coefficient': x[1],
            'templatecompcompound_ref': '~/compcompounds/id/' + x[0].id
        }, self.metabolites.items()))
        return {
            'id': self.id,
            'name': self.name,
            'GapfillDirection': self.GapfillDirection,
            'base_cost': self.base_cost,
            'reverse_penalty': self.reverse_penalty,
            'forward_penalty': self.forward_penalty,
            'deltaG': self.deltaG,
            'deltaGErr': self.deltaGErr,
            'upper_bound': self.upper_bound,
            'lower_bound': self.lower_bound,
            'direction': get_direction_from_constraints(self.lower_bound, self.upper_bound),
            'maxforflux': self.upper_bound,
            'maxrevflux': 0 if self.lower_bound > 0 else math.fabs(self.lower_bound),
            'reaction_ref': 'kbase/default/reactions/id/' + self.reference_id,
            'templateReactionReagents': template_reaction_reagents,
            'templatecompartment_ref': '~/compartments/id/' + self.compartment,
            'templatecomplex_refs': list(map(lambda x: '~/complexes/id/' + x.id, self.complexes)),
            'status': self.status,
            'type': self.type
        }

    #def build_reaction_string(self, use_metabolite_names=False, use_compartment_names=None):
    #    cpd_name_replace = {}
    #    if use_metabolite_names:
    #        if self._template:
    #            for cpd_id in set(map(lambda x: x[0], self.cstoichiometry)):
    #                name = cpd_id
    #                if cpd_id in self._template.compcompounds:
    #                    ccpd = self._template.compcompounds.get_by_id(cpd_id)
    #                    cpd = self._template.compounds.get_by_id(ccpd['templatecompound_ref'].split('/')[-1])
    #                    name = cpd.name
    #                cpd_name_replace[cpd_id] = name
    #        else:
    #            return self.data['definition']
    #    return to_str2(self, use_compartment_names, cpd_name_replace)

    #def __str__(self):
    #    return "{id}: {stoichiometry}".format(
    #        id=self.id, stoichiometry=self.build_reaction_string())


class NewModelTemplateRole:

    def __init__(self, role_id, name,
                 features=None, source='', aliases=None):
        """

        :param role_id:
        :param name:
        :param features:
        :param source:
        :param aliases:
        """
        self.id = role_id
        self.name = name
        self.source = source
        self.features = [] if features is None else features
        self.aliases = [] if aliases is None else aliases
        self._complexes = set()
        self._template = None

    @staticmethod
    def from_dict(d):
        return NewModelTemplateRole(d['id'], d['name'], d['features'], d['source'], d['aliases'])

    def get_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'aliases': self.aliases,
            'features': self.features,
            'source': self.source
        }

    def __repr__(self):
        return "<%s %s at 0x%x>" % (self.__class__.__name__, self.id, id(self))

    def __str__(self):
        return "{}:{}".format(self.id, self.name)

    def _repr_html_(self):
        return """
        <table>
            <tr>
                <td><strong>Role identifier</strong></td><td>{id}</td>
            </tr><tr>
                <td><strong>Function</strong></td><td>{name}</td>
            </tr><tr>
                <td><strong>Memory address</strong></td>
                <td>{address}</td>
            </tr><tr>
                <td><strong>In {n_complexes} complexes</strong></td><td>
                    {complexes}</td>
            </tr>
        </table>""".format(id=self.id, name=format_long_string(self.name),
                           address='0x0%x' % id(self),
                           n_complexes=len(self._complexes),
                           complexes=format_long_string(
                               ', '.join(r.id for r in self._complexes), 200))


class NewModelTemplateComplex:

    def __init__(self, complex_id, name, source='', reference='', confidence=0, template=None):
        """

        :param complex_id:
        :param name:
        :param source:
        :param reference:
        :param confidence:
        :param template:
        """
        self.id = complex_id
        self.name = name
        self.source = source
        self.reference = reference
        self.confidence = confidence
        self.roles = {}
        self._template = template

    @staticmethod
    def from_dict(d, template):
        protein_complex = NewModelTemplateComplex(
            d['id'], d['name'],
            d['source'], d['reference'], d['confidence'],
            template
        )
        for o in d['complexroles']:
            role = template.roles.get_by_id(o['templaterole_ref'].split('/')[-1])
            protein_complex.add_role(role, o['triggering'] == 1, o['optional_role'] == 1)
        return protein_complex

    def add_role(self, role: NewModelTemplateRole, triggering=True, optional=False):
        """
        Add role (function) to the complex
        :param role:
        :param triggering:
        :param optional:
        :return:
        """
        self.roles[role] = (triggering, optional)

    def get_data(self):
        complex_roles = []
        for role in self.roles:
            triggering, optional = self.roles[role]
            complex_roles.append({
                'triggering': 1 if triggering else 0,
                'optional_role': 1 if optional else 0,
                'templaterole_ref': '~/roles/id/' + role.id
            })
        return {
            'id': self.id,
            'name': self.name,
            'reference': self.reference,
            'confidence': self.confidence,
            'source': self.source,
            'complexroles': complex_roles,
        }

    def __str__(self):
        return " and ".join(map(lambda x: "{}{}{}".format(
            x[0].id,
            ":trig" if x[1][0] else "",
            ":optional" if x[1][1] else ""), self.roles.items()))

    def __repr__(self):
        return "<%s %s at 0x%x>" % (self.__class__.__name__, self.id, id(self))

    def _repr_html_(self):

        return """
        <table>
            <tr>
                <td><strong>Complex identifier</strong></td><td>{id}</td>
            </tr><tr>
                <td><strong>Name</strong></td><td>{name}</td>
            </tr><tr>
                <td><strong>Memory address</strong></td>
                <td>{address}</td>
            </tr><tr>
                <td><strong>Contains {n_complexes} role(s)</strong></td><td>
                    {complexes}</td>
            </tr>
        </table>""".format(id=self.id, name=format_long_string(self.name),
                           address='0x0%x' % id(self),
                           n_complexes=len(self.roles),
                           complexes=format_long_string(
                               ', '.join("{}:{}:{}:{}".format(r[0].id, r[0].name, r[1][0], r[1][1]) for r in
                                         self.roles.items()), 200))


class MSTemplate:

    def __init__(self, template_id, name='', domain='', template_type='', version=1, info=None, args=None):
        self.id = template_id
        self.__VERSION__ = version
        self.name = name
        self.domain = domain
        self.biochemistry_ref = ''
        self.template_type = template_type
        self.compartments = {}
        self.biomasses = DictList()
        self.reactions = DictList()
        self.compounds = DictList()
        self.compcompounds = DictList()
        self.roles = DictList()
        self.complexes = DictList()
        self.pathways = DictList()
        self.subsystems = DictList()
        #self.info = info if info else KBaseObjectInfo(object_type='KBaseFBA.NewModelTemplate')

    def add_roles(self, roles: list):
        """

        :param roles:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.roles, roles))
        if len(duplicates) > 0:
            logger.error("unable to add roles [%s] already present in the template", duplicates)
            return None

        for x in roles:
            x._template = self
        self.roles += roles

    def add_complexes(self, complexes: list):
        """

        :param complexes:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.complexes, complexes))
        if len(duplicates) > 0:
            logger.error("unable to add comp compounds [%s] already present in the template", duplicates)
            return None

        roles_to_add = []
        for x in complexes:
            x._template = self
            roles_rep = {}
            for role in x.roles:
                r = role
                if role.id not in self.roles:
                    roles_to_add.append(role)
                else:
                    r = self.roles.get_by_id(role.id)
                roles_rep[r] = x.roles[role]
                r._complexes.add(x)
            x.roles = roles_rep

        self.roles += roles_to_add
        self.complexes += complexes

    def add_compounds(self, compounds: list):
        """

        :param compounds:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.compounds, compounds))
        if len(duplicates) > 0:
            logger.error("unable to add compounds [%s] already present in the template", duplicates)
            return None

        for x in compounds:
            x._template = self
        self.compounds += compounds

    def add_comp_compounds(self, comp_compounds: list):
        """
        Add a compartment compounds (i.e., species) to the template
        :param comp_compounds:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.compcompounds, comp_compounds))
        if len(duplicates) > 0:
            logger.error("unable to add comp compounds [%s] already present in the template", duplicates)
            return None

        for x in comp_compounds:
            x._template = self
            if x.cpd_id in self.compounds:
                x._template_compound = self.compounds.get_by_id(x.cpd_id)
                x._template_compound.species.add(x)
        self.compcompounds += comp_compounds

    def add_reactions(self, reaction_list: list):
        """

        :param reaction_list:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.reactions, reaction_list))
        if len(duplicates) > 0:
            logger.error("unable to add reactions [%s] already present in the template", duplicates)
            return None

        for x in reaction_list:
            metabolites_replace = {}
            complex_replace = set()
            x._template = self
            for comp_cpd, coefficient in x.metabolites.items():
                if comp_cpd.id not in self.compcompounds:
                    self.add_comp_compounds([comp_cpd])
                metabolites_replace[self.compcompounds.get_by_id(comp_cpd.id)] = coefficient
            for cpx in x.complexes:
                if cpx.id not in self.complexes:
                    self.add_complexes([cpx])
                complex_replace.add(self.complexes.get_by_id(cpx.id))
            x._metabolites = metabolites_replace
            x.complexes = complex_replace

        self.reactions += reaction_list

    def get_role_sources(self):
        pass

    def get_complex_sources(self):
        pass

    def get_complex_from_role(self, roles):
        cpx_role_str = ';'.join(sorted(roles))
        if cpx_role_str in self.role_set_to_cpx:
            return self.role_set_to_cpx[cpx_role_str]
        return None

    @staticmethod
    def get_last_id_value(object_list, s):
        last_id = 0
        for o in object_list:
            if o.id.startswith(s):
                number_part = id[len(s):]
                if len(number_part) == 5:
                    if int(number_part) > last_id:
                        last_id = int(number_part)
        return last_id

    def get_complex(self, id):
        return self.complexes.get_by_id(id)

    def get_reaction(self, id):
        return self.reactions.get_by_id(id)

    def get_role(self, id):
        return self.roles.get_by_id(id)

    # def _to_object(self, key, data):
    #    if key == 'compounds':
    #        return NewModelTemplateCompound.from_dict(data, self)
    #    if key == 'compcompounds':
    #        return NewModelTemplateCompCompound.from_dict(data, self)
    #    #if key == 'reactions':
    #    #    return NewModelTemplateReaction.from_dict(data, self)
    #    if key == 'roles':
    #        return NewModelTemplateRole.from_dict(data, self)
    #    if key == 'subsystems':
    #        return NewModelTemplateComplex.from_dict(data, self)
    #    return super()._to_object(key, data)

    def get_data(self):
        compartments = []
        return {
            '__VERSION__': self.__VERSION__,
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'biochemistry_ref': self.biochemistry_ref,
            'type': 'Test',
            'biomasses': [],
            'compartments': [{'aliases': [],
                              'hierarchy': 3,
                              'id': 'c',
                              'index': '0',
                              'name': 'Cytosol',
                              'pH': 7},
                             {'aliases': [],
                              'hierarchy': 0,
                              'id': 'e',
                              'index': '1',
                              'name': 'Extracellular',
                              'pH': 7}],
            'compcompounds': list(map(lambda x: x.get_data(), self.compcompounds)),
            'compounds': list(map(lambda x: x.get_data(), self.compounds)),
            'roles': list(map(lambda x: x.get_data(), self.roles)),
            'complexes': list(map(lambda x: x.get_data(), self.complexes)),
            'reactions': list(map(lambda x: x.get_data(), self.reactions)),
            'pathways': [],
            'subsystems': [],
        }

    def _repr_html_(self):
        """
        taken from cobra.core.Model :)
        :return:
        """
        return """
        <table>
            <tr>
                <td><strong>ID</strong></td>
                <td>{id}</td>
            </tr><tr>
                <td><strong>Memory address</strong></td>
                <td>{address}</td>
            </tr><tr>
                <td><strong>Number of metabolites</strong></td>
                <td>{num_metabolites}</td>
            </tr><tr>
                <td><strong>Number of species</strong></td>
                <td>{num_species}</td>
            </tr><tr>
                <td><strong>Number of reactions</strong></td>
                <td>{num_reactions}</td>
            </tr><tr>
                <td><strong>Number of biomasses</strong></td>
                <td>{num_bio}</td>
            </tr><tr>
                <td><strong>Number of roles</strong></td>
                <td>{num_roles}</td>
            </tr><tr>
                <td><strong>Number of complexes</strong></td>
                <td>{num_complexes}</td>
            </tr>
          </table>""".format(
            id=self.id,
            address='0x0%x' % id(self),
            num_metabolites=len(self.compounds),
            num_species=len(self.compcompounds),
            num_reactions=len(self.reactions),
            num_bio=len(self.biomasses),
            num_roles=len(self.roles),
            num_complexes=len(self.complexes))


class MSTemplateBuilder:

    def __init__(self, template_id, name='', domain='', template_type='', version=1, info=None,
                 biochemistry=None, biomasses=None, pathways=None, subsystems=None):
        self.id = template_id
        self.version = version
        self.name = name
        self.domain = domain
        self.template_type = template_type
        self.compartments = []
        self.biomasses = []
        self.roles = []
        self.complexes = []
        self.compounds = []
        self.compartment_compounds = []
        self.reactions = []
        self.info = info
        self.biochemistry_ref = None

    @staticmethod
    def from_dict(d):
        """

        :param d:
        :param info:
        :param args:
        :return:
        """
        builder = MSTemplateBuilder(d['id'], d['name'], d['domain'], d['type'], d['__VERSION__'], None)
        builder.compartments = d['compartments']
        builder.roles = d['roles']
        builder.complexes = d['complexes']
        builder.compounds = d['compounds']
        builder.compartment_compounds = d['compcompounds']
        builder.reactions = d['reactions']
        builder.biochemistry_ref = d['biochemistry_ref']
        builder.biomasses = d['biomasses']
        return builder

    @staticmethod
    def from_template(template):
        b = MSTemplateBuilder()
        for o in template.compartments:
            b.compartments.append(copy.deepcopy(o))

        return b

    def with_compound_modelseed(self, seed_id, modelseed):
        pass

    def with_role(self, template_rxn, role_ids, auto_complex=False):
        # TODO: copy from template curation
        complex_roles = template_rxn.get_complex_roles()
        role_match = {}
        for o in role_ids:
            role_match[o] = False
        for complex_id in complex_roles:
            for o in role_match:
                if o in complex_roles[complex_id]:
                    role_match[o] = True
        all_roles_present = True
        for o in role_match:
            all_roles_present &= role_match[o]
        if all_roles_present:
            logger.debug('ignore %s all present in atleast 1 complex', role_ids)
            return None
        complex_id = self.template.get_complex_from_role(role_ids)
        if complex_id is None:
            logger.warning('unable to find complex for %s', role_ids)
            if auto_complex:
                role_names = set()
                for role_id in role_ids:
                    role = self.template.get_role(role_id)
                    role_names.add(role['name'])
                logger.warning('build complex for %s', role_names)
                complex_id = self.template.add_complex_from_role_names(role_names)
            else:
                return None
        complex_ref = '~/complexes/id/' + complex_id
        if complex_ref in template_rxn.data['templatecomplex_refs']:
            logger.debug('already contains complex %s, role %s', role_ids, complex_ref)
            return None
        return complex_ref

    def with_compound(self):
        pass

    def with_compound_compartment(self):
        pass

    def with_compartment(self, cmp_id, name, ph=7, index='0'):
        res = list(filter(lambda x: x['id'] == cmp_id, self.compartments))
        if len(res) > 0:
            return res[0]

        self.compartments.append({
            'id': cmp_id,
            'name': name,
            'aliases': [],
            'hierarchy': 3,  # TODO: what is this?
            'index': index,
            'pH': ph
        })

        return self

    def build(self):
        base = {
            '__VERSION__': '',
            'biochemistry_ref': '',
            'biomasses': [],
            'compartments': self.compartments,
            'compcompounds': [],
            'complexes': [],
            'compounds': [],
            'domain': '',
            'id': '',
            'name': '',
            'pathways': [],
            'reactions': [],
            'roles': [],
            'subsystems': [],
            'type': ''
        }

        template = MSTemplate(self.id, self.name, self.domain, self.template_type, self.version)
        template.add_compounds(list(map(lambda x: NewModelTemplateCompound.from_dict(x), self.compounds)))
        template.add_comp_compounds(
            list(map(lambda x: NewModelTemplateCompCompound.from_dict(x), self.compartment_compounds)))
        template.add_roles(list(map(lambda x: NewModelTemplateRole.from_dict(x), self.roles)))
        template.add_complexes(
            list(map(lambda x: NewModelTemplateComplex.from_dict(x, template), self.complexes)))
        template.add_reactions(
            list(map(lambda x: NewModelTemplateReaction.from_dict(x, template), self.reactions)))
        template.biomasses += list(map(lambda x: AttrDict(x), self.biomasses))  # TODO: biomass object

        return template
