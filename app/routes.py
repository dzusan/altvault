# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, session
from app import app, search
from app.forms import *
from app.update import storage_update
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
            results = octopart.search(keyword)
            init = create_part_init(results=results)
            if init:
                gen_form, info, fieldnames, add_form = init
                return render_template('add_part.html',
                                        parts=zip(gen_form.parts, info),
                                        gen_form=gen_form,
                                        fieldnames=fieldnames,
                                        add_form=add_form,
                                        searchForm=searchForm)

    locres = LocalResultForm()
    if locres.validate_on_submit():
        if storage_update(locres.table.data, locres.part.data, locres.cell.data, locres.quantity.data):
            flash('Updated {} {} in {} {}pcs'.format(locres.table.data, locres.part.data, locres.cell.data, locres.quantity.data))
    else:
        flash('Nothing changed')

    gen_form = GenForm()
    if gen_form.parts.data != 'None': # validate_on_submit() don't work !
        gen_form, info, fieldnames, add_form = create_part_init(part=gen_form.parts.data, author=gen_form.authors.data)
        return render_template('add_part.html',
                                parts=zip(gen_form.parts, info),
                                gen_form=gen_form,
                                fieldnames=fieldnames,
                                add_form=add_form,
                                searchForm=searchForm)
    else:
        flash('Nothing chosen')

    return render_template('index.html', searchForm=searchForm)


def create_part_init(results=None, part=None, author=None):
    if results:
        session['results'] = results
        resnum = results[0][1]
        if resnum == 0:
            flash('Nothing found in octopart')
            return
        else:
            part = results[1][3]
    else:
        results = session['results']
        resnum = results[0][1]
    
    flash('{} results found in octopart. First 9 below.'.format(resnum))
    results = results[1:]
    gen_form = GenForm()

    info = []
    parts = []

    for res in results:
        info.append(res[1:3])
        parts.append((res[3], res[0]))

    gen_form.parts.choices = parts
    if part:
        spec = octopart.part(part) # Octopart request 2: obtain part spec
        gen_form.parts.default = part
        gen_form.process()

    gen_form.authors.choices = selectors.author()
    if author:
        data = filler.fill_all(spec, form_author=author)
        gen_form.authors.default = author
        gen_form.process()
    else:
        data = filler.fill_all(spec)    
    
    fieldnames, add_form = gen_add_form(data=data)

    return gen_form, info, fieldnames, add_form