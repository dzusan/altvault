# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, session
from app import app, search
from app.forms import *
from app.update import storage_update, add_part
from app import selectors
import octopart
import filler


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        info = []
        forms = []
        keyword = searchForm.searchField.data
        results = search.local(keyword)
        if results:
            for res in results:
                info.append([res[1], res[3], res[4]])
                cell = res[5] if res[5] else ''
                quantity = res[6] if res[6] else 0
                forms.append(LocalResultForm(table=res[0], part=res[1], cell=cell, quantity=quantity))

            return render_template('local_results.html',
                                    res_forms=zip(info, forms),
                                    searchForm=searchForm)
        else:
            flash('Nothing found in local DB')
            results = octopart.search(keyword) # Octopart request 1: search by keyword
            init = create_part_init(results=results)
            if init:
                gen_form, info, fp_descr, add_form = init
                return render_template('add_part.html',
                                        parts=zip(gen_form.parts, info),
                                        fp_items=zip(gen_form.footprints, fp_descr),
                                        gen_form=gen_form,
                                        add_form=add_form,
                                        searchForm=searchForm)

    locres = LocalResultForm()
    if locres.validate_on_submit():
        if storage_update(locres.table.data, locres.part.data, locres.cell.data, locres.quantity.data):
            flash('Updated {} {} in {} {}pcs'.format(locres.table.data, locres.part.data, locres.cell.data, locres.quantity.data))
    else:
        flash('Nothing changed')

    gen_form = GenForm()
    if gen_form.parts.data is not None: # validate_on_submit() don't work !
    
        gen_form, info, fp_descr, add_form = create_part_init(part=gen_form.parts.data, 
                                                              author=gen_form.authors.data, 
                                                              datasheet_url=gen_form.datasheets.data,
                                                              fp_sel=gen_form.footprints.data)
        return render_template('add_part.html',
                                parts=zip(gen_form.parts, info),
                                fp_items=zip(gen_form.footprints, fp_descr),
                                gen_form=gen_form,
                                add_form=add_form,
                                searchForm=searchForm)
    else:
        flash('Nothing chosen')

    add_form = AddForm()
    if add_form.validate_on_submit():
        flash(add_part(add_form.data))

    return render_template('index.html', searchForm=searchForm)


def create_part_init(results=None, part=None, author=None, datasheet_url=None, fp_sel='0'):
    if results:
        session['results'] = results
        resnum = results[0]
        if resnum == 0:
            flash('Nothing found in octopart')
            return
        else:
            part = results[1]['uid']
    else:
        results = session['results']
        resnum = results[0]
    
    msg = '{} results found in octopart'.format(resnum)
    if resnum > 9:
        msg += '. First 9 below.'

    flash(msg)

    results = results[1:]
    parts = []
    gen_form = GenForm()

    ### Generate parts table ###

    for r in results:
        parts.append((r['uid'], r['part_number']))
    
    gen_form.parts.choices = parts
    if part:
        spec = octopart.part(part) # Octopart request 2: obtain part spec
        gen_form.parts.default = part

    ### Generate authors table ###
    gen_form.authors.choices = selectors.author()
    if author:
        data, fp_list = filler.fill_all(spec, form_author=author, fp_sel=fp_sel)
        gen_form.authors.default = author
    else:
        data, fp_list = filler.fill_all(spec, fp_sel=fp_sel)

    ### Generate datasheets table ###
    if spec['Datasheets']:
        gen_form.datasheets.choices = spec['Datasheets']
        if not datasheet_url:
            datasheet_url = spec['Datasheets'][0][0]

        gen_form.datasheets.default = datasheet_url
    
    ### Generate footprints table ###
    gen_form.footprints.choices = [(idx, item[0]) for idx, item in enumerate(fp_list)]
    fp_descr = [item[1] for item in fp_list]
    gen_form.footprints.default = fp_sel
    
    # Refresh form after adding defaults
    gen_form.process()

    # Fill the part specs
    add_form = gen_add_form(data=data)
    add_form.datasheet_url.data = datasheet_url

    return gen_form, results, fp_descr, add_form