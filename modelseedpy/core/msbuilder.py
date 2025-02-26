import logging
import itertools
import cobra
from modelseedpy.core.rast_client import RastClient
from modelseedpy.core.msgenome import normalize_role
from modelseedpy.core.msmodel import get_gpr_string, get_reaction_constraints_from_direction
from cobra.core import Gene, Metabolite, Model, Reaction
from modelseedpy.core import FBAHelper
from modelseedpy.fbapkg.mspackagemanager import MSPackageManager

SBO_ANNOTATION = "sbo"

logger = logging.getLogger(__name__)

### temp stuff ###
core_biomass = {
    'cpd00032_c0': -1.7867,
    'cpd00005_c0': -1.8225,
    'cpd00169_c0': -1.496,
    'cpd11416_c0': 1,
    'cpd00003_c0': -3.547,
    'cpd00008_c0': 41.257,
    'cpd00024_c0': -1.0789,
    'cpd00009_c0': 41.257,
    'cpd00102_c0': -0.129,
    'cpd00101_c0': -0.8977,
    'cpd00236_c0': -0.8977,
    'cpd00002_c0': -41.257,
    'cpd00022_c0': -3.7478,
    'cpd00020_c0': -2.8328,
    'cpd00006_c0': 1.8225,
    'cpd00001_c0': -41.257,
    'cpd00072_c0': -0.0709,
    'cpd00010_c0': 3.7478,
    'cpd00004_c0': 3.547,
    'cpd00061_c0': -0.5191,
    'cpd00067_c0': 46.6265,
    'cpd00079_c0': -0.205
}

core_atp = {
    'cpd00067_c0': 46.6265,
    'cpd00002_c0': -41.257,
    'cpd00008_c0': 41.257,
    'cpd00001_c0': -41.257,
    'cpd00009_c0': 41.257,
}

gramneg = {
    'cpd00166_c0': -0.00280615915959131,
    'cpd00087_c0': -0.00280615915959131,
    'cpd15560_c0': -0.00280615915959131,
    'cpd00028_c0': -0.00280615915959131,
    'cpd10515_c0': -0.00280615915959131,
    'cpd15665_c0': -0.0250105977108944,
    'cpd12370_c0': 0.00280615915959131,
    'cpd15500_c0': -0.00280615915959131,
    'cpd00220_c0': -0.00280615915959131,
    'cpd00003_c0': -0.00280615915959131,
    'cpd00557_c0': -0.00280615915959131,
    'cpd00002_c0': -40.1101757365074,
    'cpd00023_c0': -0.219088153012743,
    'cpd00062_c0': -0.0908319049068452,
    'cpd00050_c0': -0.00280615915959131,
    'cpd00008_c0': 40,
    'cpd00264_c0': -0.00280615915959131,
    'cpd00010_c0': -0.00280615915959131,
    'cpd15533_c0': -0.0311453449430676,
    'cpd11416_c0': 1,
    'cpd15540_c0': -0.0311453449430676,
    'cpd00048_c0': -0.00280615915959131,
    'cpd00035_c0': -0.427934380173264,
    'cpd17042_c0': -1,
    'cpd00030_c0': -0.00280615915959131,
    'cpd00034_c0': -0.00280615915959131,
    'cpd00161_c0': -0.211072732780569,
    'cpd00201_c0': -0.00280615915959131,
    'cpd00016_c0': -0.00280615915959131,
    'cpd00104_c0': -0.00280615915959131,
    'cpd00067_c0': 40,
    'cpd11493_c0': -0.00280615915959131,
    'cpd00051_c0': -0.246696822701341,
    'cpd00017_c0': -0.00280615915959131,
    'cpd00357_c0': -0.0157642107352084,
    'cpd17041_c0': -1,
    'cpd00038_c0': -0.135406821203723,
    'cpd00107_c0': -0.375388847540127,
    'cpd00042_c0': -0.00280615915959131,
    'cpd00149_c0': -0.00280615915959131,
    'cpd00058_c0': -0.00280615915959131,
    'cpd00041_c0': -0.200830806928348,
    'cpd00129_c0': -0.184354665339991,
    'cpd15432_c0': -0.0250105977108944,
    'cpd00052_c0': -0.0841036156544863,
    'cpd00012_c0': 0.484600235732628,
    'cpd15352_c0': -0.00280615915959131,
    'cpd00322_c0': -0.241798510337235,
    'cpd00053_c0': -0.219088153012743,
    'cpd00006_c0': -0.00280615915959131,
    'cpd00345_c0': -0.00280615915959131,
    'cpd00063_c0': -0.00280615915959131,
    'cpd00033_c0': -0.509869786991038,
    'cpd00066_c0': -0.154519490031345,
    'cpd17043_c0': -1,
    'cpd00118_c0': -0.00280615915959131,
    'cpd00009_c0': 39.9971938408404,
    'cpd15793_c0': -0.0311453449430676,
    'cpd00356_c0': -0.01627686799489,
    'cpd01997_c0': 0.00280615915959131,
    'cpd00132_c0': -0.200830806928348,
    'cpd00060_c0': -0.127801422590767,
    'cpd00037_c0': -0.00280615915959131,
    'cpd00115_c0': -0.0157642107352084,
    'cpd00099_c0': -0.00280615915959131,
    'cpd00156_c0': -0.352233189091625,
    'cpd02229_c0': -0.0250105977108944,
    'cpd00069_c0': -0.120676604606612,
    'cpd00065_c0': -0.0472019191450218,
    'cpd00241_c0': -0.01627686799489,
    'cpd15666_c0': 0.0250105977108944,
    'cpd10516_c0': -0.00280615915959131,
    'cpd00084_c0': -0.0761464922056484,
    'cpd00056_c0': -0.00280615915959131,
    'cpd00119_c0': -0.0792636000737159,
    'cpd00001_c0': -35.5403092430435,
    'cpd03422_c0': 0.00280615915959131,
    'cpd00015_c0': -0.00280615915959131,
    'cpd00054_c0': -0.179456352975885,
    'cpd00205_c0': -0.00280615915959131,
    'cpd00039_c0': -0.285438020490179,
    'cpd00254_c0': -0.00280615915959131
}

grampos = {
    'cpd00241_c0': -0.0116907079028565,
    'cpd00017_c0': -0.00719527989638797,
    'cpd00033_c0': -0.409331301687739,
    'cpd00066_c0': -0.176188648374102,
    'cpd17043_c0': -1,
    'cpd03422_c0': 0.00719527989638797,
    'cpd17041_c0': -1,
    'cpd00557_c0': -0.00719527989638797,
    'cpd00129_c0': -0.161028229793075,
    'cpd00166_c0': -0.00719527989638797,
    'cpd00030_c0': -0.00719527989638797,
    'cpd00087_c0': -0.00719527989638797,
    'cpd00015_c0': -0.00719527989638797,
    'cpd00065_c0': -0.0544955586831525,
    'cpd00357_c0': -0.0151844826784228,
    'cpd00009_c0': 41.2498047201036,
    'cpd00038_c0': -0.0424026391792249,
    'cpd15667_c0': -0.00309563020839783,
    'cpd00069_c0': -0.111039822579957,
    'cpd15540_c0': -0.0251172136637642,
    'cpd00161_c0': -0.186841915485094,
    'cpd15748_c0': -0.00309563020839783,
    'cpd00035_c0': -0.267560900902997,
    'cpd00048_c0': -0.00719527989638797,
    'cpd12370_c0': 0.00719527989638797,
    'cpd00052_c0': -0.0261242266150642,
    'cpd15757_c0': -0.00309563020839783,
    'cpd00053_c0': -0.261005044219309,
    'cpd15533_c0': -0.0251172136637642,
    'cpd00002_c0': -41.2913947104178,
    'cpd00006_c0': -0.00719527989638797,
    'cpd00084_c0': -0.0569540049395353,
    'cpd10515_c0': -0.00719527989638797,
    'cpd00104_c0': -0.00719527989638797,
    'cpd00051_c0': -0.193397772168782,
    'cpd00028_c0': -0.00719527989638797,
    'cpd00118_c0': -0.00719527989638797,
    'cpd00107_c0': -0.347460404235438,
    'cpd00037_c0': -0.00719527989638797,
    'cpd15793_c0': -0.0251172136637642,
    'cpd00010_c0': -0.00719527989638797,
    'cpd11493_c0': -0.00719527989638797,
    'cpd00264_c0': -0.00719527989638797,
    'cpd15766_c0': -0.00309563020839783,
    'cpd00041_c0': -0.14832625746843,
    'cpd00056_c0': -0.00719527989638797,
    'cpd01997_c0': 0.00719527989638797,
    'cpd15668_c0': -0.00309563020839783,
    'cpd00254_c0': -0.00719527989638797,
    'cpd11416_c0': 1,
    'cpd02229_c0': -0.00309563020839783,
    'cpd00003_c0': -0.00719527989638797,
    'cpd00008_c0': 41.257,
    'cpd17042_c0': -1,
    'cpd00023_c0': -0.261005044219309,
    'cpd15665_c0': -0.00309563020839783,
    'cpd11459_c0': -0.00309563020839783,
    'cpd15666_c0': 0.0123825208335913,
    'cpd00115_c0': -0.0151844826784228,
    'cpd00050_c0': -0.00719527989638797,
    'cpd00063_c0': -0.00719527989638797,
    'cpd00205_c0': -0.00719527989638797,
    'cpd00054_c0': -0.216753011604418,
    'cpd00042_c0': -0.00719527989638797,
    'cpd00034_c0': -0.00719527989638797,
    'cpd15500_c0': -0.00719527989638797,
    'cpd00156_c0': -0.307715523090583,
    'cpd00132_c0': -0.14832625746843,
    'cpd00067_c0': -41.257,
    'cpd15775_c0': -0.00309563020839783,
    'cpd00119_c0': -0.0819482085460939,
    'cpd00060_c0': -0.11349826883634,
    'cpd00001_c0': 45.354000686262,
    'cpd00099_c0': -0.00719527989638797,
    'cpd00356_c0': -0.0116907079028565,
    'cpd00220_c0': -0.00719527989638797,
    'cpd00322_c0': -0.27042908820211,
    'cpd00062_c0': -0.0282246669459237,
    'cpd00345_c0': -0.00719527989638797,
    'cpd00012_c0': 0.184896624320595,
    'cpd10516_c0': -0.00719527989638797,
    'cpd00039_c0': -0.323695423757071,
    'cpd00201_c0': -0.00719527989638797,
    'cpd15669_c0': -0.00309563020839783,
    'cpd15560_c0': -0.00719527989638797,
    'cpd00149_c0': -0.00719527989638797,
    'cpd00058_c0': -0.00719527989638797,
    'cpd00016_c0': -0.00719527989638797,
    'cpd15352_c0': -0.00719527989638797
}


def build_biomass(rxn_id, cobra_model, template, biomass_compounds, index='0'):
    bio_rxn = Reaction(rxn_id, 'biomass', '', 0, 1000)
    metabolites = {}
    for cpd_id in biomass_compounds:
        if cpd_id in cobra_model.metabolites:
            cpd = cobra_model.metabolites.get_by_id(cpd_id)
            metabolites[cpd] = biomass_compounds[cpd_id]
        else:
            cpd = template.compcompounds.get_by_id(cpd_id[:-1])
            compartment = f"{cpd.compartment}{index}"
            name = f"{cpd.name}_{compartment}"
            cpd = Metabolite(cpd_id, cpd.formula, name, cpd.charge, compartment)
            metabolites[cpd] = biomass_compounds[cpd_id]
    bio_rxn.add_metabolites(metabolites)
    bio_rxn.annotation[SBO_ANNOTATION] = "SBO:0000629"
    return bio_rxn


def _aaaa(genome, ontology_term):
    search_name_to_genes = {}
    search_name_to_orginal = {}
    for f in genome.features:
        if ontology_term in f.ontology_terms:
            functions = f.ontology_terms[ontology_term]
            for function in functions:
                f_norm = normalize_role(function)
                if f_norm not in search_name_to_genes:
                    search_name_to_genes[f_norm] = set()
                    search_name_to_orginal[f_norm] = set()
                search_name_to_orginal[f_norm].add(function)
                search_name_to_genes[f_norm].add(f.id)
    return search_name_to_genes, search_name_to_orginal


def aux_template(template):
    rxn_roles = {}
    roles = dict(map(lambda x: (x['id'], x), template.roles))
    for r in template.reactions:
        rxn_roles[r.id] = set()
        complex_roles = r.get_complex_roles()
        if len(complex_roles) > 0:
            for cpx_id in complex_roles:
                for role_id in complex_roles[cpx_id]:
                    rxn_roles[r.id].add(normalize_role(roles[role_id]['name']))
                    # print(role_id, normalize_role(roles[role_id]['name']))
    return rxn_roles


def build_gpr(cpx_gene_role):
    """
    example input:
     {'sdh': [{'b0721': 'sdhC', 'b0722': 'sdhD', 'b0723': 'sdhA', 'b0724': 'sdhB'}]}

     (b0721 and b0722 and b0724 and b0723)

     {'cpx1': [{'g1': 'role1', 'g3': 'role2'}, {'g2': 'role1', 'g3': 'role2'}]}

     (g1 and g3) or (g2 and g3)

    :param cpx_gene_role:
    :return:
    """
    # save cpx_id and role_id in reaction annotation for KBase object
    gpr_or_ll = []
    for cpx_id in cpx_gene_role:
        # print(cpx_id)
        for complex_set in cpx_gene_role[cpx_id]:
            # print(complex_set)
            gpr_or_ll.append("({})".format(' and '.join(set(complex_set))))

    return ' or '.join(gpr_or_ll)


class MSBuilder:

    def __init__(self, genome, template=None):
        """
        for future methods with better customization
        """
        self.genome = genome
        self.template = template
        self.search_name_to_genes, self.search_name_to_original = _aaaa(genome, 'RAST')

    def _get_template_reaction_complexes(self, template_reaction):
        """

        :param template_reaction:
        :return:
        """
        template_reaction_complexes = {}
        for cpx in template_reaction.get_complexes():
            template_reaction_complexes[cpx.id] = {}
            for role, (triggering, optional) in cpx.roles.items():
                sn = normalize_role(role.name)
                template_reaction_complexes[cpx.id][role.id] = [
                    sn,
                    triggering,
                    optional,
                    set() if sn not in self.search_name_to_genes else set(self.search_name_to_genes[sn])
                ]
        return template_reaction_complexes

    @staticmethod
    def _build_reaction_complex_gpr_sets(match_complex, allow_incomplete_complexes=True):
        complexes = {}
        for cpx_id in match_complex:
            complete = True
            roles = set()
            role_genes = {}
            for role_id in match_complex[cpx_id]:
                t = match_complex[cpx_id][role_id]
                complete &= len(t[3]) > 0 or not t[1] or t[2]  # true if has genes or is not triggering or is optional
                # print(t[3])
                if len(t[3]) > 0:
                    roles.add(role_id)
                    role_genes[role_id] = t[3]
                # print(t)
            # it is never complete if has no genes, only needed if assuming a complex can have all
            # roles be either non triggering or optional
            logger.debug('[%s] maps to %s and complete: %s', cpx_id, roles, complete)
            if len(roles) > 0 and (allow_incomplete_complexes or complete):
                logger.debug('[%s] role_genes: %s', cpx_id, role_genes)
                ll = []
                for role_id in role_genes:
                    role_gene_set = []
                    for gene_id in role_genes[role_id]:
                        role_gene_set.append({gene_id: role_id})
                    ll.append(role_gene_set)
                logger.debug('[%s] complex lists: %s', cpx_id, ll)
                complexes[cpx_id] = list(
                    map(lambda x: dict(map(lambda o: list(o.items())[0], x)), itertools.product(*ll)))
        return complexes

    def get_gpr_from_template_reaction(self, template_reaction, allow_incomplete_complexes=True):
        template_reaction_complexes = self._get_template_reaction_complexes(template_reaction)
        if len(template_reaction_complexes) == 0:
            return None

        # self.map_gene(template_reaction_complexes)
        # print(template_reaction_complexes)
        gpr_set = self._build_reaction_complex_gpr_sets(template_reaction_complexes, allow_incomplete_complexes)
        return gpr_set

    @staticmethod
    def _build_reaction(reaction_id, gpr_set, template, index='0', sbo=None):
        template_reaction = template.reactions.get_by_id(reaction_id)

        reaction_compartment = template_reaction.compartment
        metabolites = {}

        for cpd, value in template_reaction.metabolites.items():
            compartment = f"{cpd.compartment}{index}"
            name = f"{cpd.name}_{compartment}"
            cpd = Metabolite(cpd.id + str(index), cpd.formula, name, cpd.charge, compartment)
            metabolites[cpd] = value

        reaction = Reaction(
            "{}{}".format(template_reaction.id, index),
            "{}_{}{}".format(template_reaction.name, reaction_compartment, index),
            '',
            template_reaction.lower_bound, template_reaction.upper_bound
        )

        gpr_str = build_gpr(gpr_set) if gpr_set else ''
        reaction.add_metabolites(metabolites)
        if gpr_str and len(gpr_str) > 0:
            reaction.gene_reaction_rule = gpr_str  # get_gpr_string(gpr_ll)

        reaction.annotation["seed.reaction"] = template_reaction.reference_id
        if sbo:
            reaction.annotation[SBO_ANNOTATION] = sbo
        return reaction

    @staticmethod
    def build_exchanges(model, extra_cell='e0'):
        """
        Build exchange reactions for the "extra_cell" compartment
        :param model: Cobra Model
        :param extra_cell: compartment representing extracellular
        :return:
        """
        reactions_exchanges = []
        for m in model.metabolites:
            if m.compartment == extra_cell:
                rxn_exchange = Reaction('EX_' + m.id, 'Exchange for ' + m.name, 'exchanges', -1000, 1000)
                rxn_exchange.add_metabolites({m: -1})
                rxn_exchange.annotation[SBO_ANNOTATION] = "SBO:0000627"
                reactions_exchanges.append(rxn_exchange)
        model.add_reactions(reactions_exchanges)

        return reactions_exchanges

    @staticmethod
    def build_biomasses(model, template, index):
        res = []
        if template.name.startswith('CoreModel'):
            res.append(build_biomass('bio1', model, template, core_biomass, index))
            res.append(build_biomass('bio2', model, template, core_atp, index))
        if template.name.startswith('GramNeg'):
            res.append(build_biomass('bio1', model, template, gramneg, index))
        if template.name.startswith('GramPos'):
            res.append(build_biomass('bio1', model, template, grampos, index))
        return res

    def build(self, model_id, index='0', allow_all_non_grp_reactions=False, annotate_with_rast=True):

        if annotate_with_rast:
            rast = RastClient()
            res = rast.annotate_genome(self.genome)
            self.search_name_to_genes, self.search_name_to_original = _aaaa(self.genome, 'RAST')

        # rxn_roles = aux_template(self.template)  # needs to be fixed to actually reflect template GPR rules
        from modelseedpy.helpers import get_template, get_classifier
        from modelseedpy.core.mstemplate import MSTemplateBuilder
        genome_classifier = get_classifier('knn_filter')
        genome_class = genome_classifier.classify(self.genome)

        template_genome_scale_map = {
            'N': 'template_gram_neg',
            'P': 'template_gram_pos',
        }
        template_core_map = {
            'N': 'template_core',
            'P': 'template_core',
        }

        if self.template is None and genome_class in template_genome_scale_map and genome_class in template_core_map:
            self.template = MSTemplateBuilder.from_dict(get_template(template_genome_scale_map[genome_class])).build()
        elif self.template is None:
            raise Exception(f'unable to select template for {genome_class}')

        metabolic_reactions = {}
        for template_reaction in self.template.reactions:
            gpr_set = self.get_gpr_from_template_reaction(template_reaction)
            if gpr_set:
                metabolic_reactions[template_reaction.id] = gpr_set
                logger.debug("[%s] gpr set: %s", template_reaction.id, gpr_set)

        reactions = list(map(
            lambda x: self._build_reaction(x[0], x[1], self.template, index, "SBO:0000176"),
            metabolic_reactions.items()))

        cobra_model = Model(model_id)
        cobra_model.add_reactions(reactions)

        reactions_no_gpr = []
        reactions_in_model = set(map(lambda x: x.id, cobra_model.reactions))
        metabolites_in_model = set(map(lambda x: x.id, cobra_model.metabolites))

        for rxn in self.template.reactions:
            if rxn.type == 'universal' or rxn.type == 'spontaneous':
                reaction = self._build_reaction(rxn.id, {}, self.template, index, "SBO:0000176")
                reaction_metabolite_ids = set(map(lambda x: x.id, set(reaction.metabolites)))
                if (len(metabolites_in_model & reaction_metabolite_ids) > 0 or allow_all_non_grp_reactions) and \
                        reaction.id not in reactions_in_model:
                    reaction.annotation["seed.reaction"] = rxn.id
                    reactions_no_gpr.append(reaction)
        cobra_model.add_reactions(reactions_no_gpr)

        cobra_model.add_reactions(self.build_exchanges(cobra_model))

        if self.template.name.startswith('CoreModel') or \
                self.template.name.startswith('GramNeg') or self.template.name.startswith('GramPos'):
            cobra_model.add_reactions(self.build_biomasses(cobra_model, self.template, index))
            cobra_model.objective = 'bio1'

        reactions_sinks = []
        for cpd_id in ['cpd02701_c0', 'cpd11416_c0', 'cpd15302_c0']:
            if cpd_id in cobra_model.metabolites:
                m = cobra_model.metabolites.get_by_id(cpd_id)
                rxn_exchange = Reaction('SK_' + m.id, 'Sink for ' + m.name, 'exchanges', 0, 1000)
                rxn_exchange.add_metabolites({m: -1})
                rxn_exchange.annotation[SBO_ANNOTATION] = "SBO:0000627"
                reactions_sinks.append(rxn_exchange)
        cobra_model.add_reactions(reactions_sinks)

        return cobra_model
    
    @staticmethod
    def build_full_template_model(template):
        model = Model(template.id)
        all_reactions = []
        for rxn in template.reactions:
            reaction = MSBuilder._build_reaction(rxn.id, {}, template, "0", "SBO:0000176")
            reaction.annotation["seed.reaction"] = rxn.id
            all_reactions.append(reaction)
        model.add_reactions(all_reactions)
        reactions_exchanges = []
        for m in model.metabolites:
            if m.compartment == 'e0':
                rxn_exchange = Reaction('EX_' + m.id, 'Exchange for ' + m.name, 'exchanges', -1000, 1000)
                rxn_exchange.add_metabolites({m: -1})
                rxn_exchange.annotation[SBO_ANNOTATION] = "SBO:0000627"
                reactions_exchanges.append(rxn_exchange)
        model.add_reactions(reactions_exchanges)
        
        if self.template.name.startswith('CoreModel'):
            bio_rxn1 = build_biomass('bio1', cobra_model, self.template, core_biomass, index)
            bio_rxn2 = build_biomass('bio2', cobra_model, self.template, core_atp, index)
            model.add_reactions([bio_rxn1, bio_rxn2])
            model.objective = 'bio1'
        if self.template.name.startswith('GramNeg'):
            bio_rxn1 = build_biomass('bio1', cobra_model, self.template, gramneg, index)
            model.add_reactions([bio_rxn1])
            model.objective = 'bio1'
        if self.template.name.startswith('GramPos'):
            bio_rxn1 = build_biomass('bio1', cobra_model, self.template, grampos, index)
            model.add_reactions([bio_rxn1])
            model.objective = 'bio1'
        
        reactions_sinks = []
        for cpd_id in ['cpd02701_c0', 'cpd11416_c0', 'cpd15302_c0']:
            if cpd_id in model.metabolites:
                m = model.metabolites.get_by_id(cpd_id)
                rxn_exchange = Reaction('SK_' + m.id, 'Sink for ' + m.name, 'exchanges', 0, 1000)
                rxn_exchange.add_metabolites({m: -1})
                rxn_exchange.annotation[SBO_ANNOTATION] = "SBO:0000627"
                reactions_sinks.append(rxn_exchange)
        model.add_reactions(reactions_sinks)
        return model

    @staticmethod
    def build_metabolic_model(model_id, genome, gapfill_media=None, template=None, index='0',
                              allow_all_non_grp_reactions=False, annotate_with_rast=True, gapfill_model=True):
        builder = MSBuilder(genome, template)
        model = builder.build(model_id, index, allow_all_non_grp_reactions, annotate_with_rast)
        # Gapfilling model
        if gapfill_model:
            model = MSBuilder.gapfill_model(model, 'bio1', builder.template, gapfill_media)
        return model

    @staticmethod
    def gapfill_model(original_mdl, target_reaction, template, media):
        FBAHelper.set_objective_from_target_reaction(original_mdl, target_reaction)
        model = cobra.io.json.from_json(cobra.io.json.to_json(original_mdl))
        pkgmgr = MSPackageManager.get_pkg_mgr(model)
        pkgmgr.getpkg("GapfillingPkg").build_package({
            "default_gapfill_templates": [template],
            "gapfill_all_indecies_with_default_templates": 1,
            "minimum_obj": 0.01,
            "set_objective": 1
        })
        pkgmgr.getpkg("KBaseMediaPkg").build_package(media)
        #with open('Gapfilling.lp', 'w') as out:
        #    out.write(str(model.solver))
        sol = model.optimize()
        gfresults = pkgmgr.getpkg("GapfillingPkg").compute_gapfilled_solution()
        for rxnid in gfresults["reversed"]:
            rxn = original_mdl.reactions.get_by_id(rxnid)
            if gfresults["reversed"][rxnid] == ">":
                rxn.upper_bound = 100
            else:
                rxn.lower_bound = -100
        for rxnid in gfresults["new"]:
            rxn = model.reactions.get_by_id(rxnid)
            rxn = rxn.copy()
            original_mdl.add_reactions([rxn])
            if gfresults["new"][rxnid] == ">":
                rxn.upper_bound = 100
                rxn.lower_bound = 0 
            else:
                rxn.upper_bound = 0
                rxn.lower_bound = -100
        return original_mdl