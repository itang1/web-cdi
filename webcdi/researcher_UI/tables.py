import django_tables2 as tables
from cdi_forms import views
from django_tables2.utils import A
from django.conf.urls import url
from .models import administration

# Table for organizing administration objects into a table on the researcher interface
class StudyAdministrationTable(tables.Table):
    select_col = tables.columns.CheckBoxColumn(accessor='id') # Creates a column of checkboxes associated with each administration ID
    link = tables.TemplateColumn('<a href="/form/fill/{{ record.url_hash }}" target="_blank">link</a>', orderable=False) # Generates a column of administration links in each row

    # Associates administration table with administration model
    class Meta:
        model = administration
        exclude = ("study",'id', 'url_hash','completedBackgroundInfo', 'page_number', 'bypass', 'include') # Excludes some fields in administration objects from table
        sequence = ('select_col','subject_id', 'repeat_num', 'link',) # Specifies column order within table
