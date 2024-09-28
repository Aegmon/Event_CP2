from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Events8, Users2, Attendee_events5, Client_events4, Supplier_info, Event_records2, Attendee_records2
from . import db
from .gen_algo import *
import json
import csv
from datetime import datetime

views_supplier = Blueprint('views_supplier', __name__)

######################################################################################################################################################### Supplier

@views_supplier.route('/supplier', methods=['GET', 'POST'])
def supplier():
    # Check if the user already has supplier information
    supplier_info = Supplier_info.query.filter_by(user_id=current_user.id).first()

    if supplier_info:
        # If supplier information exists, render the profile page with all supplier data
        return render_template('supplier_prof.html', user=current_user, 
                               supplier_type=supplier_info.supplier_type,
                               av_commission=supplier_info.av_commission,
                               nickname=supplier_info.nickname,
                               phone_number=supplier_info.phone_number,
                               email_sup=supplier_info.email_sup,
                               self_desc=supplier_info.self_desc)
    else:
        # If no supplier information exists, handle the POST request or render the supplier form
        if request.method == 'POST':
            supplier_type = request.form.get('supplier_type')
            av_commission = request.form.get('av_commission')
            nickname = request.form.get('nickname')
            phone_number = request.form.get('phone_number')
            email_sup = request.form.get('email_sup')
            self_desc = request.form.get('self_desc')
            
            new_supplier = Supplier_info(
                supplier_type=supplier_type,
                av_commission=av_commission,
                nickname=nickname,
                phone_number=phone_number,
                email_sup=email_sup,
                self_desc=self_desc,
                user_id=current_user.id  # Associate the supplier with the current user
            )
            db.session.add(new_supplier)
            db.session.commit()

            # Prepare the data to append to the CSV file
            data_to_append = [nickname, "0", av_commission]

            # Open the CSV file in append mode
            with open(csv_file_path, 'a', newline='') as file:
                writer = csv.writer(file)
                # Append the new row
                writer.writerow(data_to_append)

            return render_template('supplier_prof.html', user=current_user, 
                                   supplier_type=supplier_type, 
                                   av_commission=av_commission, 
                                   nickname=nickname, 
                                   phone_number=phone_number, 
                                   email_sup=email_sup, 
                                   self_desc=self_desc)

        return render_template('supplier.html', user=current_user)