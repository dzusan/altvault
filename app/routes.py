# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for
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
                                    title='Search results',
                                    res_forms=zip(info, forms),
                                    searchForm=searchForm)
        else:
            flash('Nothing found in local DB')
            results = octopart.search(keyword)
            resnum = results[0][1]
            print(results[0][0], results[0][1])
            if resnum == 0:
                flash('Nothing found in octopart')
            else:
                flash('{} results found in octopart. First 9 below.'.format(resnum))
                results = results[1:]
                gen_form = GenForm()
                parts = []
                for res in results:
                    info.append(res[1:3])
                    parts.append((res[3], res[0]))

                gen_form.parts.choices = parts
                gen_form.authors.choices = selectors.author()
                fieldnames, add_form = gen_add_form()
                return render_template('add_part.html',
                                        title='Search results',
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
        flash(gen_form.parts.data)
        flash(gen_form.authors.data)
        info = octopart.part(gen_form.parts.data)
        print(filler.fill_all(gen_form.authors.data, info)) 

    else:
        flash('Nothing chosen')

    return render_template('index.html', title='Home', searchForm=searchForm)
