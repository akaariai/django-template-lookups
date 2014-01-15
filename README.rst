django-template-lookups
=======================

Template lookups for Django 1.7+

Allows one to write lookups and transforms in declarative way.

A quick example::

    from template_lookups import TemplateLookup, TemplateTransform
    from django.db.models import Field, IntegerField

    class YearExtract(TemplateTransform):
        lookup_name = 'year'
        template = 'EXTRACT(YEAR FROM {lhs})'
        output_type = IntegerField()


    class OptimizedYearExact(TemplateLookup):
        # This one works only using PostgreSQL. If you need support for
        # other databases, just add more template_vendorname attributes
        # to this class.
        lookup_name = 'exact'
        template_postgresql = (
            "{lhs_lhs} >= to_date({rhs} || '-01-01', 'yyyy-mm-dd') "
            "AND {lhs_lhs} < to_date(({rhs} + 1) || '-01-01', 'yyyy-mm-dd')")

    class DayExact(TemplateLookup):
        lookup_name = 'day_exact'
        template = 'EXTRACT(DAY FROM {lhs}) = {rhs}'
        rhs_type = IntegerField()

    Field.register_lookup(DayExact)
    Field.register_lookup(YearExtract)
    YearExtract.register_lookup(OptimizedYearExact)

The lookups produce output like this::

    class AModel(models.Model):
        datefield = models.DateField()

    print AModel.objects.filter(datefield__year__exact=2012).query
    out: SELECT ... FROM "tester_amodel"
          WHERE "tester_amodel"."datefield" >= to_date(2012 || '-01-01', 'yyyy-mm-dd')
                AND "tester_amodel"."datefield" < to_date((2012 + 1) || '-01-01', 'yyyy-mm-dd')
    print AModel.objects.filter(datefield__year__lte=2013).query
    out: SELECT ... FROM "tester_amodel"
          WHERE EXTRACT(YEAR FROM "tester_amodel"."datefield") <= 2013
    print AModel.objects.filter(datefield__day_exact=11).query
    out: SELECT ... FROM "tester_amodel"
          WHERE EXTRACT(DAY FROM "tester_amodel"."datefield") = 11
