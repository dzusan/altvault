# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for
from app import app, search
from app.forms import *
from app.update import storage_update


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

            return render_template('results.html',
                                    title='Search results',
                                    res_forms=zip(info, forms),
                                    searchForm=searchForm)
        else:
            flash('Nothing found in local DB')

    res_form = LocalResultForm()
    if res_form.validate_on_submit():
        if storage_update(res_form.table.data, res_form.part.data, res_form.cell.data, res_form.quantity.data):
            flash('Updated {} {} in {} {}pcs'.format(res_form.table.data, res_form.part.data, res_form.cell.data, res_form.quantity.data))
    else:
        flash('Nothing changed')

    return render_template('index.html', title='Home', searchForm=searchForm)
