# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import AddStudyForm, RenameStudyForm, AddPairedStudyForm
from .models import study, administration, administration_data, get_meta_header, get_background_header, payment_code, ip_address
import codecs, json, os, re, random, csv, datetime, cStringIO
from .tables  import StudyAdministrationTable
from django_tables2   import RequestConfig
from django.db.models import Max
from cdi_forms.views import model_map, get_model_header, background_info_form, prefilled_background_form
from cdi_forms.models import BackgroundInfo
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
import pandas as pd
import numpy as np
from django.core.urlresolvers import reverse
from decimal import Decimal
from django.contrib.sites.shortcuts import get_current_site
from ipware.ip import get_ip




@login_required # For researchers only, requires user to be logged in (test-takers do not have an account and are blocked from this interface)
def download_data(request, study_obj, administrations = None): # Download study data
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv') # Format response as a CSV
    response['Content-Disposition'] = 'attachment; filename='+study_obj.name+'_data.csv''' # Name the CSV response
    
    model_header = get_model_header(study_obj.instrument.name) # Fetch the associated instrument model's variables
    
    # Fetch administration variables
    admin_header = ['study_name', 'subject_id','repeat_num', 'administration_id', 'link', 'completed', 'completedBackgroundInfo', 'due_date', 'last_modified','created_date']
    # background_header = [col for col in BackgroundInfo._meta.get_all_field_names() if col not in ['administration_id', 'administration']]

    # Fetch background data variables
    background_header = ['age','sex','zip_code','birth_order','multi_birth_boolean','multi_birth', 'birth_weight', 'born_on_due_date', 'early_or_late', 'due_date_diff', 'mother_yob', 'mother_education','father_yob', 'father_education', 'annual_income', 'child_hispanic_latino', 'child_ethnicity', 'caregiver_info', 'other_languages_boolean','other_languages','language_from', 'language_days_per_week', 'language_hours_per_day', 'ear_infections_boolean','ear_infections', 'hearing_loss_boolean','hearing_loss', 'vision_problems_boolean','vision_problems', 'illnesses_boolean','illnesses', 'services_boolean','services','worried_boolean','worried','learning_disability_boolean','learning_disability']

    # Try to properly format CDI responses for pandas dataframe
    try:
        answers = administration_data.objects.values('administration_id', 'item_ID', 'value').filter(administration_id__in = administrations)
        melted_answers = pd.DataFrame.from_records(answers).pivot(index='administration_id', columns='item_ID', values='value')
        melted_answers.reset_index(level=0, inplace=True)
    except:
        melted_answers = pd.DataFrame(columns = get_model_header(study_obj.instrument.name))

    # Format background data responses for pandas dataframe and eventual printing
    try:
        background_data = BackgroundInfo.objects.values().filter(administration__in = administrations)
        new_background = pd.DataFrame.from_records(background_data)

        for c in new_background.columns:
            try:
                new_background = new_background.replace({c: dict(BackgroundInfo._meta.get_field(c).choices)}) # Replaces integer and single letter responses in dataframe with more easily interpreted choices that were originally given to test-takers. For instance, gender in database is stored as 'M' but is presented to test-takers and researchers as 'Male' for a lesser chance of misinterpretation
            except:
                if 'boolean' in c or c == 'born_on_due_date': # Replace integer boolean responses with text responses (catches any columns missed by previous pass)
                    new_background = new_background.replace({c: {0: 'No', 1: 'Yes', 2: 'Prefer not to disclose'}})
                elif c == 'child_hispanic_latino':
                    new_background = new_background.replace({c: {False: 'No', True: 'Yes'}})

    except:
        new_background(columns = ['administration_id'] + background_header)


    # Try to combine background data and CDI responses
    background_answers = pd.merge(new_background, melted_answers, how='outer', on = 'administration_id')

    # Try to format administration data for pandas dataframe
    try:
        admin_data = pd.DataFrame.from_records(administrations.values()).rename(columns = {'id':'administration_id', 'study_id': 'study_name', 'url_hash': 'link'})
    except:
        admin_data = pd.DataFrame(columns = admin_header)
    
    # Replace study ID# with actual study name
    admin_data['study_name'] = study_obj.name

    # Merge administration data into already combined background/CDI form dataframe
    combined_data = pd.merge(admin_data, background_answers, how='outer', on = 'administration_id')

    # Recreate link for administration
    test_url = ''.join(['http://', get_current_site(request).domain, reverse('administer_cdi_form', args=['a'*64])]).replace('a'*64+'/','')
    combined_data['link'] = test_url + combined_data['link']

    # If there are any missing columns (e.g., all test-takers for one study did not answer an item so it does not appear in database responses), add the empty columns in and don't break!
    missing_columns = list(set(model_header) - set(combined_data.columns))
    if missing_columns:
        combined_data = combined_data.reindex(columns = np.append( combined_data.columns.values, missing_columns))
    print "tweaked data!"

    # Organize columns  
    combined_data = combined_data[admin_header + background_header + model_header ]
    print "reorganized column!"

    # Turn pandas dataframe into a CSV
    combined_data.to_csv(response, encoding='utf-8')

    # Return CSV
    return response



@login_required
def download_dictionary(request, study_obj): # Download dictionary for instrument, lists relevant information for each item
    response = HttpResponse(content_type='text/csv') # Format the response as a CSV
    response['Content-Disposition'] = 'attachment; filename='+study_obj.instrument.name+'_dictionary.csv''' # Name CSV

    raw_item_data = model_map(study_obj.instrument.name).objects.values('itemID','item_type','category','definition','gloss') # Grab the relevant variables within the appropriate instrument model
    pd.DataFrame.from_records(raw_item_data).to_csv(response, encoding='utf-8') # Convert nested dictionary into a pandas dataframe and then into a CSV

    # Return CSV
    return response    

@login_required
def download_links(request, study_obj, administrations = None): # Download only the associated administration links instead of the whole data spreadsheet

    response = HttpResponse(content_type='text/csv') # Format response as a CSV
    response['Content-Disposition'] = 'attachment; filename='+study_obj.name+'_links.csv''' # Name CSV

    admin_data = pd.DataFrame.from_records(administrations.values()).rename(columns = {'id':'administration_id', 'study_id': 'study_name', 'url_hash': 'link'}) # Grab variables from administration objects
    admin_data = admin_data[['study_name','subject_id', 'repeat_num', 'administration_id','link']] # Organize columns

    admin_data['study_name'] = study_obj.name # Replace study ID number with actual study name

    # Recreate administration links and add them to dataframe
    test_url = ''.join(['http://', get_current_site(request).domain, reverse('administer_cdi_form', args=['a'*64])]).replace('a'*64+'/','')
    admin_data['link'] = test_url + admin_data['link']
    admin_data.to_csv(response, encoding='utf-8') # Convert dataframe into a CSV

    # Return CSV
    return response

 
@login_required
def console(request, study_name = None, num_per_page = 20):
    refresh = False
    if request.method == 'POST' :
        data = {}
        permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
        study_obj = study.objects.get(researcher= request.user, name= study_name)
        if permitted :
            if request.method == 'POST' :
                ids = request.POST.getlist('select_col')
                if 'administer-selected' in request.POST:
                    if all([x.isdigit() for x in ids]):
                        num_ids = map(int, ids)
                        new_administrations = []
                        sids_created = set()
                        for nid in num_ids:
                            admin_instance = administration.objects.get(id = nid)
                            sid = admin_instance.subject_id
                            if sid in sids_created:
                                continue
                            old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count()
                            new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = old_rep+1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=14)))
                            sids_created.add(sid)


                        administration.objects.bulk_create(new_administrations)
                        refresh = True

                elif 'delete-selected' in request.POST:
                    ids = request.POST.getlist('select_col')
                    if all([x.isdigit() for x in ids]):
                        ids = list(set(map(int, ids)))
                        administration.objects.filter(id__in = ids).delete()
                        # for nid in ids:
                        #     admin_object = administration.objects.get(id = nid)
                        #     admin_object.delete()
                        refresh = True

                elif 'download-links' in request.POST:
                    ids = request.POST.getlist('select_col')
                    administrations = []
                    if all([x.isdigit() for x in ids]):
                        ids = list(set(map(int, ids)))
                        administrations = administration.objects.filter(id__in = ids)
                        return download_links(request, study_obj, administrations)
                        refresh = True


                elif 'download-selected' in request.POST:
                    ids = request.POST.getlist('select_col')
                    if all([x.isdigit() for x in ids]):
                        ids = list(set(map(int, ids)))
                        administrations = administration.objects.filter(id__in = ids)
                        return download_data(request, study_obj, administrations)
                        refresh = True

                elif 'delete-study' in request.POST:
                    study_obj.delete()
                    study_name = None
                    refresh = True

                elif 'download-study' in request.POST:
                    administrations = administration.objects.filter(study = study_obj)
                    return download_data(request, study_obj, administrations)

                elif 'download-dictionary' in request.POST:
                    return download_dictionary(request, study_obj)

                elif 'view_all' in request.POST:
                    if request.POST['view_all'] == "Show All":
                        num_per_page = administration.objects.filter(study = study_obj).count()
                    elif request.POST['view_all'] == "Show 20":
                        num_per_page = 20
                    refresh = True

        
    if request.method == 'GET' or refresh:
        username = None
        if request.user.is_authenticated():
            username = request.user.username
        context = dict()
        context['username'] =  username 
        context['studies'] = study.objects.filter(researcher = request.user).order_by('id')
        context['instruments'] = []
        if study_name is not None:
            try:
                current_study = study.objects.get(researcher= request.user, name= study_name)
                administration_table = StudyAdministrationTable(administration.objects.filter(study = current_study))
                if not current_study.confirm_completion:
                    administration_table.exclude = ("study",'id', 'url_hash','completedBackgroundInfo', 'analysis')
                RequestConfig(request, paginate={'per_page': num_per_page}).configure(administration_table)
                context['current_study'] = current_study.name
                context['num_per_page'] = num_per_page
                context['study_instrument'] = current_study.instrument.verbose_name
                context['study_group'] = current_study.study_group
                context['study_administrations'] = administration_table
                context['completed_admins'] = administration.objects.filter(study = current_study, completed = True).count()
                context['unique_children'] = count = administration.objects.filter(study = current_study, completed = True).values('subject_id').distinct().count()
                context['allow_payment'] = current_study.allow_payment
                context['available_giftcards'] = payment_code.objects.filter(hash_id__isnull = True, study = current_study).count()
            except:
                pass
        return render(request, 'researcher_UI/interface.html', context)

@login_required 
def rename_study(request, study_name):
    data = {}
    form_package = {}
    #check if the researcher exists and has permissions over the study
    permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
    study_obj = study.objects.get(researcher= request.user, name= study_name)
    if request.method == 'POST' :
        form = RenameStudyForm(study_name, request.POST, instance = study_obj)
        raw_gift_codes = None
        all_new_codes = None
        old_codes = None
        amount_regex = None
        if form.is_valid():
            researcher = request.user
            new_study_name = form.cleaned_data.get('name')
            raw_gift_codes = form.cleaned_data.get('gift_codes')
            raw_gift_amount = form.cleaned_data.get('gift_amount')
            raw_test_period = form.cleaned_data.get('test_period')

            study_obj = form.save(commit=False)
            study_obj.test_period = raw_test_period if (raw_test_period >= 1 and raw_test_period <= 30) else 14

            if new_study_name != study_name:
                if study.objects.filter(researcher = researcher, name = study_obj.name).exists():
                    study_obj.name = study_name

            study_obj.save()

            new_study_name = study_obj.name

            if raw_gift_codes:
                new_payment_codes = []
                used_codes = []
                gift_codes = re.split('[,;\s\t\n]+', raw_gift_codes)
                gift_regex = re.compile(r'^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{6}-[a-zA-Z0-9]{4}$')
                gift_type = "Amazon"
                gift_codes = filter(gift_regex.search, gift_codes)                

                try:
                    amount_regex = Decimal(re.search('([0-9]{1,3})?.[0-9]{2}', raw_gift_amount).group(0))
                except:
                    pass

                if amount_regex:

                    for gift_code in gift_codes:
                        if not payment_code.objects.filter(payment_type = gift_type, gift_code = gift_code).exists():
                            new_payment_codes.append(payment_code(study =study_obj, payment_type = gift_type, gift_code = gift_code, gift_amount = amount_regex))
                        else:
                            used_codes.append(gift_code)
                if not used_codes:
                    all_new_codes = True


            if raw_gift_codes:
                if not all_new_codes or not amount_regex: 
                    data['stat'] = "error";
                    err_msg = []
                    if not all_new_codes:
                        err_msg = err_msg + ['The following codes are already in the database:'] + used_codes;
                    if not amount_regex:
                        err_msg = err_msg + [ "Please enter in a valid amount for \"Amount per Card\""];

                    data['error_message'] = "<br>".join(err_msg);
                    return HttpResponse(json.dumps(data), content_type="application/json")
                else:
                    if all_new_codes:
                        payment_code.objects.bulk_create(new_payment_codes)
                        data['stat'] = "ok";
                        data['redirect_url'] = "/interface/study/"+new_study_name+"/";
                        return HttpResponse(json.dumps(data), content_type="application/json") 
            else:
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/study/"+new_study_name+"/";
                return HttpResponse(json.dumps(data), content_type="application/json")            

        else:
            data['stat'] = "re-render";
            form_package['form'] = form
            form_package['form_name'] = 'Update Study'
            form_package['allow_payment'] = study_obj.allow_payment
            return render(request, 'researcher_UI/add_study_modal.html', form_package)
    else:

        form = RenameStudyForm(instance = study_obj, old_study_name = study_obj.name)
        form_package['form'] = form
        form_package['form_name'] = 'Update Study'
        form_package['allow_payment'] = study_obj.allow_payment
        return render(request, 'researcher_UI/add_study_modal.html', form_package)
        
@login_required 
def add_study(request):
    data = {}
    if request.method == 'POST' :
        form = AddStudyForm(request.POST)
        if form.is_valid():
            study_instance = form.save(commit=False)
            researcher = request.user
            study_name = form.cleaned_data.get('name')
            study_instance.researcher = researcher

            if not study.objects.filter(researcher = researcher, name = study_name).exists():

                study_instance.save()
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/study/"+study_name+"/";
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                data['stat'] = "error";
                data['error_message'] = "Study already exists; Use a unique name";
                return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data['stat'] = "re-render";
            return render(request, 'researcher_UI/add_study_modal.html', {'form': form, 'form_name': 'Add New Study'})
    else:
        form = AddStudyForm()
        return render(request, 'researcher_UI/add_study_modal.html', {'form': form, 'form_name': 'Add New Study'})


@login_required 
def add_paired_study(request):
    data = {}
    researcher = request.user

    if request.method == 'POST' :
        form = AddPairedStudyForm(request.POST)
        if form.is_valid():
            study_group = form.cleaned_data.get('study_group')
            paired_studies = form.cleaned_data.get('paired_studies')
            permissions = []
            for one_study in paired_studies:
                permitted = study.objects.filter(researcher = researcher,  name = one_study).exists()
                permissions.append(permitted)
                if permitted:
                    study_obj = study.objects.get(researcher = researcher,  name = one_study)                    
                    study_obj.study_group = study_group
                    study_obj.save()

            if all(True for permission in permissions):
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/";
                return HttpResponse(json.dumps(data), content_type="application/json")

            else:
                data['stat'] = "error";
                data['error_message'] = "Study group already exists; Use a unique name";
                return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            print form
            data['stat'] = "re-render";
            return render(request, 'researcher_UI/add_paired_study_modal.html', {'form': form})
    else:
        form = AddPairedStudyForm(researcher = researcher)
        return render(request, 'researcher_UI/add_paired_study_modal.html', {'form': form})

def random_url_generator(size=64, chars='0123456789abcdef'):
    return ''.join(random.choice(chars) for _ in range(size))


@login_required 
def administer_new(request, study_name):
    data = {}
    context = dict()
    #check if the researcher exists and has permissions over the study
    permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
    study_obj = study.objects.get(researcher= request.user, name= study_name)

    if request.method == 'POST' :
        if permitted :
            params = dict(request.POST)
            validity = True
            data['error_message'] = ''
            raw_ids_csv = request.FILES['subject-ids-csv'] if 'subject-ids-csv' in request.FILES else None

            if params['new-subject-ids'][0] == '' and params['autogenerate-count'][0] == '' and raw_ids_csv is None:
                validity = False
                data['error_message'] += "Form is empty\n"

            if raw_ids_csv:
                if 'csv-header' in request.POST:
                    ids_df = pd.read_csv(raw_ids_csv)
                    if request.POST['subject-ids-column']:
                        subj_column = request.POST['subject-ids-column']
                        if subj_column in ids_df.columns:
                            ids_to_add = ids_df[subj_column]
                            ids_type =  ids_to_add.dtype
                        else:
                            ids_type = 'missing'

                    else:
                        ids_to_add = ids_df[ids_df.columns[0]]
                        ids_type =  ids_to_add.dtype

                else:
                    ids_df = pd.read_csv(raw_ids_csv, header = None)
                    ids_to_add = ids_df[ids_df.columns[0]]
                    ids_type =  ids_to_add.dtype

                if ids_type != 'int64':
                    validity = False
                    if 'csv-header' not in request.POST:
                        data['error_message'] += "Non integer subject ids. Make sure first row is numeric\n"
                    else:
                        if ids_type == 'missing':
                            data['error_message'] += "Unable to find specified column. Check for any typos."
                        else:
                            data['error_message'] += "Non integer subject ids\n"


            if params['new-subject-ids'][0] != '':
                subject_ids = re.split('[,;\s\t\n]+', str(params['new-subject-ids'][0]))
                subject_ids = filter(None, subject_ids)
                subject_ids_numbers = all([x.isdigit() for x in subject_ids])
                if not subject_ids_numbers:
                    validity = False
                    data['error_message'] += "Non integer subject ids\n"

            if params['autogenerate-count'][0] != '':
                autogenerate_count = params['autogenerate-count'][0]
                autogenerate_count_isdigit = autogenerate_count.isdigit()
                if not autogenerate_count_isdigit:
                    validity = False
                    data['error_message'] += "Non integer number of IDs to autogenerate\n"

            if validity:
                new_administrations = []
                test_period = int(study_obj.test_period)
                if raw_ids_csv:

                    subject_ids = ids_to_add.tolist()

                    for sid in subject_ids:
                        new_hash = random_url_generator()
                        old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count()
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = old_rep+1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now()+ datetime.timedelta(days=test_period)))

                if params['new-subject-ids'][0] != '':
                    subject_ids = re.split('[,;\s\t\n]+', str(params['new-subject-ids'][0]))
                    subject_ids = filter(None, subject_ids)
                    subject_ids = map(int, subject_ids)
                    for sid in subject_ids:
                        new_hash = random_url_generator()
                        old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count()
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = old_rep+1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now()+ datetime.timedelta(days=test_period)))


                if params['autogenerate-count'][0]!='':
                    autogenerate_count = int(params['autogenerate-count'][0])
                    max_subject_id = administration.objects.filter(study=study_obj).aggregate(Max('subject_id'))['subject_id__max']
                    if max_subject_id is None:
                        max_subject_id = 0
                    for sid in range(max_subject_id+1, max_subject_id+autogenerate_count+1):
                        new_hash = random_url_generator()
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = 1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=test_period)))

                administration.objects.bulk_create(new_administrations)
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/study/"+study_name+"/?sort=-created_date";
                data['study_name'] = study_name
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                data['stat'] = "error";
                return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data['stat'] = "error";
            data['error_message'] = "permission denied";
            data['redirect_url'] = "interface/";
            return HttpResponse(json.dumps(data), content_type="application/json")
    else:
        context['username'] = request.user.username
        context['study_name'] = study_name
        context['study_group'] = study_obj.study_group
        return render(request, 'researcher_UI/administer_new_modal.html', context)

def administer_new_parent(request, username, study_name):
    data={}
    new_administrations = []
    autogenerate_count = 1
    researcher = User.objects.get(username = username)
    study_obj = study.objects.get(name= study_name, researcher = researcher)
    subject_cap = study_obj.subject_cap
    test_period = int(study_obj.test_period)
    completed_admins = administration.objects.filter(study = study_obj, completed = True).count()
    bypass = request.GET.get('bypass', None)
    let_through = None
    prev_visitor = 0
    visitor_ip = str(get_ip(request))
    completed = int(request.get_signed_cookie('completed_num', '0'))
    if visitor_ip:
        prev_visitor = ip_address.objects.filter(ip_address = visitor_ip).count()

    if (prev_visitor < 1 and completed < 2) or request.user.is_authenticated():
        if completed_admins < subject_cap:
            let_through = True
        elif subject_cap is None:
            let_through = True
        elif bypass:
            let_through = True

    if let_through:
        max_subject_id = administration.objects.filter(study=study_obj).aggregate(Max('subject_id'))['subject_id__max']
        if max_subject_id is None:
            max_subject_id = 0
        new_admin = administration.objects.create(study =study_obj, subject_id = max_subject_id+1, repeat_num = 1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=test_period))
        new_hash_id = new_admin.url_hash
        if bypass:
            new_admin.bypass = True
            new_admin.save()
        redirect_url = reverse('administer_cdi_form', args=[new_hash_id])
    else:
        redirect_url = reverse('overflow', args=[username, study_name])
    return redirect(redirect_url)

def overflow(request, username, study_name):
    data = {}
    data['username'] = username
    data['study_name'] = study_name
    visitor_ip = str(get_ip(request))
    prev_visitor = 0
    if (visitor_ip and visitor_ip != 'None'):
        prev_visitor = ip_address.objects.filter(ip_address = visitor_ip).count()
    if prev_visitor > 0 and not request.user.is_authenticated():
        data['repeat'] = True


    return render(request, 'cdi_forms/overflow.html', data)

