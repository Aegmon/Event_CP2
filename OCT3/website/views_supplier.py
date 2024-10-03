from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from .models import Note, Events11, Users6, Attendee_events6, Client_events4, Supplier_info6, Event_records2, Attendee_records2
from . import db
from .gen_algo_final import *
import json
import csv
from flask_socketio import join_room, leave_room, send, SocketIO
from datetime import datetime

views_supplier = Blueprint('views_supplier', __name__)

Thing = namedtuple('Thing', ['name', 'rating', 'price'])

supplier_things = []
supplier_cake = []
supplier_digital_printing = []
supplier_event_planner = []
supplier_grazing_table = []
supplier_makeup_and_hair = []
supplier_photobooth = []
supplier_photographer = []
supplier_catering = []
supplier_church = []
supplier_event_stylist = []
supplier_events_place = []
supplier_lights_and_sounds = []
supplier_others = []


def append_info():
    # Query all supplier information
    supplier_information = Supplier_info6.query.all()
    print(supplier_information)

    # Loop through each supplier and create a named tuple for each
    for supplier in supplier_information:
        new_thing = Thing(
            name=supplier.fullname,
            rating=supplier.rating,
            price=int(supplier.commission)  # Ensure the commission is converted to int
        )

        # Append to the supplier_things array
        supplier_things.append(new_thing)

        # Append to specific supplier type arrays
        if supplier.supplier_type == "Cake":
            supplier_cake.append(new_thing)
        elif supplier.supplier_type == "Digital_Printing":
            supplier_digital_printing.append(new_thing)
        elif supplier.supplier_type == "Event_Planner":
            supplier_event_planner.append(new_thing)
        elif supplier.supplier_type == "Grazing_Table":
            supplier_grazing_table.append(new_thing)
        elif supplier.supplier_type == "Makeup_and_Hair":
            supplier_makeup_and_hair.append(new_thing)
        elif supplier.supplier_type == "Photobooth":
            supplier_photobooth.append(new_thing)
        elif supplier.supplier_type == "Photographer":
            supplier_photographer.append(new_thing)
        elif supplier.supplier_type == "Catering":
            supplier_catering.append(new_thing)
        elif supplier.supplier_type == "Church":
            supplier_church.append(new_thing)
        elif supplier.supplier_type == "Event_Stylist":
            supplier_event_stylist.append(new_thing)
        elif supplier.supplier_type == "Events_Place":
            supplier_events_place.append(new_thing)
        elif supplier.supplier_type == "Lights_and_Sounds":
            supplier_lights_and_sounds.append(new_thing)
        elif supplier.supplier_type == "Others":
            supplier_others.append(new_thing)

@views_supplier.route('/create_event_profile_supplier')
@login_required
def create_event_profile_supplier():
    # Get the current user
    user = current_user

    # Pass the user data and images to the template
    return render_template('create_event_profile.html', user=user)
######################################################################################################################################################### Supplier

@views_supplier.route('/supplier', methods=['GET', 'POST'])
@login_required
def supplier():
    # Check if the user already has supplier information
    supplier_info6 = Supplier_info6.query.filter_by(user_id=current_user.id).first()

    # If the supplier information exists, redirect to supplier profile page
    if supplier_info6:
        return render_template('supplier_prof.html', 
                               user=current_user,
                               fullname=supplier_info6.fullname,
                               supplier_type=supplier_info6.supplier_type,
                               commission=supplier_info6.commission,
                               phone_number=supplier_info6.phone_number,
                               phone_number2=supplier_info6.phone_number2,
                               email_sup=supplier_info6.email_sup,
                               self_desc=supplier_info6.supplier_description,
                               extra_info=supplier_info6.extra_info,
                               rating=supplier_info6.rating)  # Use supplier_info6 rating

    # If supplier information doesn't exist, handle new entry
    if request.method == 'POST':
        fullname = current_user.first_name + " " + current_user.last_name
        supplier_type = request.form.get('supplier_type')
        commission = request.form.get('commission')
        phone_number = request.form.get('phone_number')
        phone_number2 = request.form.get('phone_number2')
        email_sup = request.form.get('email_sup')
        supplier_description = request.form.get('supplier_description')
        extra_info = request.form.get('extra_info')
        rating = 0  # Default rating for new suppliers

        # Validation checks
        if not commission.isdigit():
            flash('Commission must be a whole number (integer).', category='error')
            return redirect(url_for('views_supplier.supplier'))

        if len(phone_number) > 11 or len(phone_number2) > 11:
            flash('Phone numbers must not exceed 11 characters.', category='error')
            return redirect(url_for('views_supplier.supplier'))

        # Proceed if validation passes
        new_supplier = Supplier_info6(
            fullname=fullname,
            supplier_type=supplier_type,
            commission=commission,
            phone_number=phone_number,
            phone_number2=phone_number2,
            email_sup=email_sup,
            supplier_description=supplier_description,
            extra_info=extra_info,
            user_id=current_user.id,
            rating=rating  # Associate the supplier with the current user
        )
        db.session.add(new_supplier)
        db.session.commit()

        data_to_append = [fullname, "0", commission]

        # Open the CSV file in append mode
        with open(csv_file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            # Append the new row
            writer.writerow(data_to_append)

        # Append to specific supplier type CSVs based on the supplier_type
            if supplier_type == "Cake":
                supplier_csv = cake
            elif supplier_type == "Digital_Printing":
                supplier_csv = digital_printing
            elif supplier_type == "Event_Planner":
                supplier_csv = event_planner
            elif supplier_type == "Grazing_Table":
                supplier_csv = grazing_table
            elif supplier_type == "Makeup_and_Hair":
                supplier_csv = makeup_and_Hair
            elif supplier_type == "Photobooth":
                supplier_csv = photobooth
            elif supplier_type == "Photographer":
                supplier_csv = photographer
            elif supplier_type == "Catering":
                supplier_csv = catering
            elif supplier_type == "Church":
                supplier_csv = church
            elif supplier_type == "Event_Stylist":
                supplier_csv = event_stylist
            elif supplier_type == "Events_Place":
                supplier_csv = events_place
            elif supplier_type == "Lights_and_Sounds":
                supplier_csv = lights_and_sounds
            else:
                supplier_csv = None

            # Append data to the specific supplier type CSV file if a match is found
            if supplier_csv:
                with open(supplier_csv, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(data_to_append)
            
            def read_csv(file_path, arr):
                with open(file_path, mode='r', newline='') as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    for row in csv_reader:
                        thing = Thing(name=row['name'], rating=int(row['rating']), price=float(row['price']))
                        arr.append(thing)
            
            read_csv(csv_file_path, things_list)
            read_csv(cake , cake_arr)
            read_csv(digital_printing , digital_printing_arr)
            read_csv(event_planner , event_planner_arr)
            read_csv(grazing_table , grazing_table_arr)
            read_csv(makeup_and_Hair , makeup_and_hair_arr)
            read_csv(photobooth , photobooth_arr)
            read_csv(photographer , photographer_arr)

            read_csv(catering, catering_arr)
            read_csv(church, church_arr)
            read_csv(event_stylist, event_stylist_arr)
            read_csv(events_place, events_place_arr)
            read_csv(lights_and_sounds, lights_and_sounds_arr)


        # Append to specific supplier type arrays based on the supplier_type

        return redirect(url_for('views_supplier.supplier'))  # Redirect to avoid resubmission on refresh

    return render_template('supplier.html', user=current_user)

@views_supplier.route('/supplier_rating_feedback', methods=['GET'])
@login_required
def supplier_rating_feedback():
    # Fetch the logged-in supplier's info (assuming the current user is a supplier)
    supplier_info = Supplier_info6.query.filter_by(user_id=current_user.id).all()

    if not supplier_info:
        flash('You have no reviews or feedback yet.', category='info')
        return redirect(request.url)

    return render_template('supplier_rating_feedback.html', user=current_user, supplier_info=supplier_info)