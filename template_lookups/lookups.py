from django.db.models import Lookup, Transform
import re

lookup_template_re = re.compile(r'({\s*lhs_lhs\s*})|({\s*lhs\s*})|({\s*rhs\s*})')
transform_template_re = re.compile(r'({\s*lhs\s*})')

class TemplateLookup(Lookup):
    """
    TemplateLookup allows one to write lookups in shorter way than
    plain Lookups. For example:
        class YearExactLookup(TemplateLookup):
            lookup_name = 'year_exact'
            template = 'EXTRACT(YEAR FROM {lhs}) = {rhs}'

    If you want different templates for different databases, then
    you can use template_vendorname.

    In addition skipping lhs's extract is supported if that is
    needed. You can use {lhs_lhs} to do that.

    There is no way to escape {lhs}, {rhs} or {lhs_lhs}
    currently. So, I hope you won't need those exact strings
    in your project.
    """
    template = None
    _compile_cache = {}

    @classmethod
    def _compile_template(cls, vendor):
        if (cls, vendor) in cls._compile_cache:
            return cls._compile_cache[(cls, vendor)]
        template = getattr(cls, 'template_' + vendor, cls.template)
        res = re.findall(lookup_template_re, template)
        param_order = []
        for match in res:
            if match[0]:
                param_order.append('lhs_lhs')
            elif match[1]:
                param_order.append('lhs')
            elif match[2]:
                param_order.append('rhs')
        cls._compile_cache[(cls, vendor)] = (template, param_order)
        return template, param_order

    def as_sql(self, qn, connection):
        template, param_order = self._compile_template(connection.vendor)
        format_kwargs = {}
        params_dict = {}
        if 'lhs' in param_order:
            lhs, lhs_params = self.process_lhs(qn, connection)
            format_kwargs['lhs'] = lhs
            params_dict['lhs'] = lhs_params
        if 'rhs' in param_order:
            rhs, rhs_params = self.process_rhs(qn, connection)
            format_kwargs['rhs'] = rhs
            params_dict['rhs'] = rhs_params
        if 'lhs_lhs' in param_order:
            lhs_lhs, lhs_lhs_params = qn.compile(self.lhs.lhs)
            format_kwargs['lhs_lhs'] = lhs_lhs
            params_dict['lhs_lhs'] = lhs_lhs_params
        params = []
        for thing in param_order:
            params.extend(params_dict[thing])
        return template.format(**format_kwargs), params


class TemplateTransform(Transform):
    template = None
    _compile_cache = {}

    @classmethod
    def _compile_template(cls, vendor):
        if vendor in cls._compile_cache:
            return cls._compile_cache[vendor]
        template = getattr(cls, 'template_' + vendor, cls.template)
        res = re.findall(transform_template_re, template)
        param_order = []
        for match in res:
            param_order.append('lhs')
        cls._compile_cache[vendor] = (template, param_order)
        return template, param_order

    def as_sql(self, qn, connection):
        template, param_order = self._compile_template(connection.vendor)
        format_kwargs = {}
        params_dict = {}
        if 'lhs' in param_order:
            lhs, lhs_params = qn.compile(self.lhs)
            format_kwargs['lhs'] = lhs
            params_dict['lhs'] = lhs_params
        params = []
        for thing in param_order:
            params.extend(params_dict[thing])
        return template.format(**format_kwargs), params
