from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Events8, Users2, Attendee_events5, Client_events4, Supplier_info, Event_records2, Attendee_records2
from . import db
from .gen_algo import *
from .algo_cake import *
from .algo_digital_printing import *
from .algo_event_planner import *
from .algo_grazing_table import *
from .algo_makeup_and_hair import *
from .algo_photobooth import *
from .algo_photographer import *
import json
import csv
from datetime import datetime

views_creator = Blueprint('views_creator', __name__)

########################################################################################################################################################################### Event Creator

@views_creator.route('/create_event_home', methods=['GET', 'POST'])
@login_required
def create_event_home():
    return render_template('create_event_home.html', user=current_user, name=current_user.first_name)
###########################################################################################################################################################################
@views_creator.route('/create-event', methods=['GET', 'POST'])
@login_required
def event():
    if request.method == 'POST':
        # Get form inputs
        event_name = request.form.get('event_name')
        event_desc = request.form.get('event_desc')
        event_type = request.form.get('event_type')
        event_privacy = request.form.get('event_privacy')  # New input for event status
        cake_gen = request.form.get('cake_gen')
        digital_printing_gen = request.form.get('digital_printing_gen')
        event_planner_gen = request.form.get('event_planner_gen')
        grazing_table_gen = request.form.get('grazing_table_gen')
        makeup_and_hair_gen = request.form.get('makeup_and_hair_gen')
        photobooth_gen = request.form.get('photobooth_gen')
        photographer_gen = request.form.get('photographer_gen')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        max_attendee_num_str = request.form.get('max_attendee_num')
        selected_attendees = request.form.getlist('attendees')

        # Validate maximum attendees
        try:
            max_attendee_num = int(max_attendee_num_str)
            if max_attendee_num < 1:
                flash('Maximum Attendees must be at least 1.', category='error')
                return redirect(request.url)
        except ValueError:
            flash('Maximum Attendees must be a valid whole number (no decimals).', category='error')
            return redirect(request.url)
        # Convert date strings to datetime objects
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Please provide valid start and end dates.', category='error')
            return redirect(request.url)
        # Ensure the end date is after the start date
        if end_date < start_date:
            flash('End date cannot be before start date.', category='error')
            return redirect(request.url)

        # Fetch attendee details from the database based on the selected IDs
        attendee_details = []
        for attendee_id in selected_attendees:
            attendee = Users2.query.get(attendee_id)
            if attendee:
                attendee_details.append({
                    'id': attendee.id,
                    'name': attendee.first_name,
                    'lname': attendee.last_name,
                    'email': attendee.email
                })

        # Convert selected attendee details to JSON
        invited_attendees_json = json.dumps(attendee_details)

        #Initialize Answers
        cake_answers = []
        digital_printing_answers = []
        event_planner_answers = []
        grazing_table_answers = []
        makeup_and_hair_answers = []
        photobooth_answers = []
        photographer_answers = []

        #All Algos For Generations Of Suppliers
        if cake_gen:
            price_limit_cake = 6500
            fitness_limit_cake = 500  # Adjust fitness limit to reflect more restrictive price limit
            population_size_cake = 20  # Increase population size for better exploration
            generation_limit_cake = 200  # Increase generation limit for thorough search

            population, generations = run_evolution_cake(
            populate_func=partial(
                generate_population_cake, size=population_size_cake, genome_length=len(cake1)
            ),
            fitness_func=partial(
                fitness_cake, cake1=cake1, price_limit_cake=price_limit_cake
            ),
            fitness_limit_cake=fitness_limit_cake,
            generation_limit_cake=generation_limit_cake
            )
            cake_answers = genome_to_things_cake(population[0], cake1)
        
        if digital_printing_gen:
            price_limit_digital_printing = 5000
            fitness_limit_digital_printing = 500  # Adjust fitness limit to reflect more restrictive price limit
            population_size_digital_printing = 20  # Increase population size for better exploration
            generation_limit_digital_printing = 200  # Increase generation limit for thorough search

            population, generations = run_evolution_digital_printing(
            populate_func=partial(
                generate_population_digital_printing, size=population_size_digital_printing, genome_length=len(digital_printing1)
            ),
            fitness_func=partial(
                fitness_digital_printing, digital_printing1=digital_printing1, price_limit_digital_printing=price_limit_digital_printing
            ),
            fitness_limit_digital_printing=fitness_limit_digital_printing,
            generation_limit_digital_printing=generation_limit_digital_printing
            )
            digital_printing_answers = genome_to_things_digital_printing(population[0], digital_printing1)

        if event_planner_gen:
            price_limit_event_planner = 30000
            fitness_limit_event_planner = 100  # Adjust fitness_event_planner limit to reflect more restrictive price limit
            population_size_event_planner = 80  # Increase population size for better exploration
            generation_limit_event_planner = 200  # Increase generation limit for thorough search

            population, generations = run_evolution_event_planner(
            populate_func=partial(
                generate_population_event_planner, size=population_size_event_planner, genome_length=len(event_planner1)
            ),
            fitness_func=partial(
                fitness_event_planner, event_planner1=event_planner1, price_limit_event_planner=price_limit_event_planner
            ),
            fitness_limit_event_planner=fitness_limit_event_planner,
            generation_limit_event_planner=generation_limit_event_planner
            )
            event_planner_answers = genome_to_things_event_planner(population[0], event_planner1)
        
        if grazing_table_gen:
            price_limit_grazing_table = 12000
            fitness_limit_grazing_table = 500  # Adjust fitness_grazing_table limit to reflect more restrictive price limit
            population_size_grazing_table = 20  # Increase population size for better exploration
            generation_limit_grazing_table = 200  # Increase generation limit for thorough search

            population, generations = run_evolution_grazing_table(
            populate_func=partial(
                generate_population_grazing_table, size=population_size_grazing_table, genome_length=len(grazing_table1)
            ),
            fitness_func=partial(
                fitness_grazing_table, grazing_table1=grazing_table1, price_limit_grazing_table=price_limit_grazing_table
            ),
            fitness_limit_grazing_table=fitness_limit_grazing_table,
            generation_limit_grazing_table=generation_limit_grazing_table
            )
            grazing_table_answers = genome_to_things_grazing_table(population[0], grazing_table1)

        if makeup_and_hair_gen:
            price_limit_makeup_and_hair = 30000
            fitness_limit_makeup_and_hair = 1000  # Adjust fitness_makeup_and_hair limit to reflect more restrictive price limit
            population_size_makeup_and_hair = 100  # Increase population size for better exploration
            generation_limit_makeup_and_hair = 200  # Increase generation limit for thorough search

            population, generations = run_evolution_makeup_and_hair(
            populate_func=partial(
                generate_population_makeup_and_hair, size=population_size_makeup_and_hair, genome_length=len(makeup_and_hair1)
            ),
            fitness_func=partial(
                fitness_makeup_and_hair, makeup_and_hair1=makeup_and_hair1, price_limit_makeup_and_hair=price_limit_makeup_and_hair
            ),
            fitness_limit_makeup_and_hair=fitness_limit_makeup_and_hair,
            generation_limit_makeup_and_hair=generation_limit_makeup_and_hair
            )
            makeup_and_hair_answers = genome_to_things_makeup_and_hair(population[0], makeup_and_hair1)

        if photobooth_gen:
            price_limit_photobooth = 6000
            fitness_limit_photobooth = 500  # Adjust fitness_photobooth limit to reflect more restrictive price limit
            population_size_photobooth = 80  # Increase population size for better exploration
            generation_limit_photobooth = 200  # Increase generation limit for thorough search

            population, generations = run_evolution_photobooth(
            populate_func=partial(
                generate_population_photobooth, size=population_size_photobooth, genome_length=len(photobooth1)
            ),
            fitness_func=partial(
                fitness_photobooth, photobooth1=photobooth1, price_limit_photobooth=price_limit_photobooth
            ),
            fitness_limit_photobooth=fitness_limit_photobooth,
            generation_limit_photobooth=generation_limit_photobooth
            )
            photobooth_answers = genome_to_things_photobooth(population[0], photobooth1)
        
        if photographer_gen:
            price_limit_photographer = 18000
            fitness_limit_photographer = 100  # Adjust fitness_photographer_photographer limit to reflect more restrictive price limit
            population_size_photographer = 120  # Increase population size for better exploration
            generation_limit_photographer = 250  # Increase generation limit for thorough search

            population, generations = run_evolution_photographer(
            populate_func=partial(
                generate_population_photographer, size=population_size_photographer, genome_length=len(photographer1)
            ),
            fitness_func=partial(
                fitness_photographer_photographer, photographer1=photographer1, price_limit_photographer=price_limit_photographer
            ),
            fitness_limit_photographer=fitness_limit_photographer,
            generation_limit_photographer=generation_limit_photographer
            )
            photographer_answers = genome_to_things_photographer(population[0], photographer1)

        best_answers = cake_answers + digital_printing_answers + event_planner_answers + grazing_table_answers + makeup_and_hair_answers + photobooth_answers + photographer_answers

        # Convert the list of best answers to JSON
        answers_json = json.dumps(best_answers)

        # Create new event instance and save it to the database
        new_event = Events8(
            event_name=event_name,
            event_desc=event_desc,
            event_type=event_type,
            event_privacy=event_privacy,  # Save event status
            data1=answers_json,
            user_id=current_user.id,
            max_attendee_num=max_attendee_num,
            start_date=start_date,
            end_date=end_date,
            invited_attendees=invited_attendees_json  # Save the selected attendees as JSON
        )
        db.session.add(new_event)
        db.session.commit()

        # Save the event to Event_records2 as well
        new_event_record = Event_records2(
            event_name=event_name,
            event_desc=event_desc,
            event_type=event_type,
            event_privacy=event_privacy,
            start_date=start_date,
            end_date=end_date,
            creator_id=current_user.id  # Save the creator's user ID
        )
        db.session.add(new_event_record)

        db.session.commit()

        flash('Event added!', category='success')
        # Now store this event in each selected attendee's Attendee_events5 "invites" field
        for attendee_id in selected_attendees:
            attendee = Users2.query.get(attendee_id)
            if attendee:
                # Get or create the Attendee_events5 entry for this user
                attendee_event = Attendee_events5.query.filter_by(user_id=attendee.id).first()
                if not attendee_event:
                    attendee_event = Attendee_events5(user_id=attendee.id, invites='[]')
                    db.session.add(attendee_event)
                
                # Load the current invites
                invites = json.loads(attendee_event.invites)

                # Add the new event to the invites list
                invites.append({
                    'event_name': event_name,
                    'event_desc': event_desc,
                    'event_privacy': event_privacy,
                    'start_date': start_date.strftime('%Y-%m-%d %H:%M'),
                    'end_date': end_date.strftime('%Y-%m-%d %H:%M')
                })

                # Save back the updated invites list
                attendee_event.invites = json.dumps(invites)

        db.session.commit()

        flash('Event added and invites sent!', category='success')

        # Query all attendees with the role 'Attendee'
    attendees = Users2.query.filter_by(role='Attendee').all()

    return render_template("create-event.html", user=current_user, name=current_user.first_name, attendees=attendees)
###########################################################################################################################################################################
@views_creator.route('/created_event_edit', methods=['GET', 'POST'])
@login_required
def created_event_edit():
    # Fetch and display the user's existing events
    user_events = current_user.events
    events_data = []

    for event in user_events:
        event_data = json.loads(event.data1)

        cake_thing = []
        digital_printing_thing = []
        event_planner_thing = []
        grazing_table_thing = []
        makeup_and_hair_thing = []
        photobooth_thing = []
        photographer_thing = []
        catering_thing = []
        church_thing = []
        event_stylist_thing = []
        events_place_thing = []
        lights_and_sounds_thing = []

        for item in event_data:
            for supplier in cake1:
                if supplier.name == item:
                    cake_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in digital_printing1:
                if supplier.name == item:
                    digital_printing_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in event_planner1:
                if supplier.name == item:
                    event_planner_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in grazing_table1:
                if supplier.name == item:
                    grazing_table_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in makeup_and_hair1:
                if supplier.name == item:
                    makeup_and_hair_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in photobooth1:
                if supplier.name == item:
                    photobooth_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in photographer1:
                if supplier.name == item:
                    photographer_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in catering1:
                if supplier.name == item:
                    catering_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in church1:
                if supplier.name == item:
                    church_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in event_stylist1:
                if supplier.name == item:
                    event_stylist_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in events_place1:
                if supplier.name == item:
                    events_place_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in lights_and_sounds1:
                if supplier.name == item:
                    lights_and_sounds_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})

        attendee_data = json.loads(event.invited_attendees)
        
        # Calculate total weight from the suppliers' arrays
        total_price = (
            sum(supplier['price'] for supplier in cake_thing) +
            sum(supplier['price'] for supplier in digital_printing_thing ) +
            sum(supplier['price'] for supplier in event_planner_thing ) +
            sum(supplier['price'] for supplier in grazing_table_thing ) +
            sum(supplier['price'] for supplier in makeup_and_hair_thing ) +
            sum(supplier['price'] for supplier in photobooth_thing ) +
            sum(supplier['price'] for supplier in photographer_thing ) +
            sum(supplier['price'] for supplier in catering_thing ) +
            sum(supplier['price'] for supplier in church_thing ) +
            sum(supplier['price'] for supplier in event_stylist_thing ) +
            sum(supplier['price'] for supplier in events_place_thing  ) +
            sum(supplier['price'] for supplier in lights_and_sounds_thing )
        )
        
        events_data.append({
            'event_name': event.event_name,
            'event_desc': event.event_desc,
            'event_type': event.event_type,
            'event_privacy': event.event_privacy,
            'data1': event_data,
            'id': event.id,
            'total_price': total_price,
            'rsvp_attendees': event.rsvp_attendees,
            'invited_attendees': attendee_data,
            'max_attendee_num': event.max_attendee_num,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'cake_thing': cake_thing,
            'digital_printing_thing': digital_printing_thing,
            'event_planner_thing': event_planner_thing,
            'grazing_table_thing': grazing_table_thing,
            'makeup_and_hair_thing': makeup_and_hair_thing,
            'photobooth_thing': photobooth_thing,
            'photographer_thing': photographer_thing,
            'catering_thing': catering_thing,
            'church_thing': church_thing,
            'event_stylist_thing': event_stylist_thing,
            'events_place_thing': events_place_thing,
            'lights_and_sounds_thing': lights_and_sounds_thing

        })
    return render_template('create_event_edit.html', user=current_user, name=current_user.first_name, events=events_data, cake1=cake1, 
                                                    digital_printing1=digital_printing1, event_planner1=event_planner1, 
                                                    grazing_table1=grazing_table1, makeup_and_hair1=makeup_and_hair1, 
                                                    photobooth1=photobooth1, photographer1=photographer1, catering1=catering1, 
                                                    church1=church1, event_stylist1=event_stylist1, events_place1=events_place1, 
                                                    lights_and_sounds1=lights_and_sounds1)
###########################################################################################################################################################################
@views_creator.route('/add_supplier_to_event/<int:event_id>/<string:supplier_name>', methods=['POST'])
@login_required
def add_supplier_to_event(event_id, supplier_name):
    event = Events8.query.get(event_id)

    if not event:
        return jsonify({'success': False, 'message': 'Event not found.'})

    # Load existing data1
    event_data = json.loads(event.data1)

    # Check which supplier category to add the supplier to (assumes supplier_name matches the category)
    supplier_type = None
    for supplier in cake1:
        if supplier.name == supplier_name:
            supplier_type = 'cake_thing'
            break
    for supplier in digital_printing1:
        if supplier.name == supplier_name:
            supplier_type = 'digital_printing_thing'
            break
    for supplier in event_planner1:
        if supplier.name == supplier_name:
            supplier_type = 'event_planner_thing'
            break
    for supplier in grazing_table1:
        if supplier.name == supplier_name:
            supplier_type = 'grazing_table_thing'
            break
    for supplier in makeup_and_hair1:
        if supplier.name == supplier_name:
            supplier_type = 'makeup_and_hair_thing'
            break
    for supplier in photobooth1:
        if supplier.name == supplier_name:
            supplier_type = 'photobooth_thing'
            break
    for supplier in photographer1:
        if supplier.name == supplier_name:
            supplier_type = 'photographer_thing'
            break
    for supplier in catering1:
        if supplier.name == supplier_name:
            supplier_type = 'catering_thing'
            break
    for supplier in church1:
        if supplier.name == supplier_name:
            supplier_type = 'church_thing'
            break
    for supplier in event_stylist1:
        if supplier.name == supplier_name:
            supplier_type = 'event_stylist_thing'
            break
    for supplier in events_place1:
        if supplier.name == supplier_name:
            supplier_type = 'events_place_thing'
            break
    for supplier in lights_and_sounds1:
        if supplier.name == supplier_name:
            supplier_type = 'lights_and_sounds_thing'
            break
    
    if supplier_type:
        # Check if the supplier is already in the event data
        if supplier_name in event_data:
            return jsonify({'success': False, 'message': 'Supplier already added to the event.'})

        # Append supplier name to the event data
        event_data.append(supplier_name)  # Assuming you want to append the supplier name to data1
        event.data1 = json.dumps(event_data)  # Convert back to JSON
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Supplier not found.'})
###########################################################################################################################################################################
@views_creator.route('/creator_delete_supplier/<int:event_id>/<string:supplier_name>', methods=['POST'])
@login_required
def creator_delete_supplier(event_id, supplier_name):
    # Fetch the event by ID
    event = Events8.query.filter_by(id=event_id, user_id=current_user.id).first()

    if not event:
        return jsonify({'success': False, 'message': 'Event not found'}), 404

    # Load the current event data1 field (JSON stored in the database)
    event_data = json.loads(event.data1)

    # Remove the supplier from the event data if it exists
    if supplier_name in event_data:
        event_data.remove(supplier_name)

        # Update the event data1 field with the modified data
        event.data1 = json.dumps(event_data)
        db.session.commit()  # Save changes to the database

        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Supplier not found in event data'}), 400
###########################################################################################################################################################################
@views_creator.route('/delete_event_created/<int:event_id>', methods=['POST'])
@login_required
def delete_event_created(event_id):
    # Find the event by its ID
    event = Events8.query.get(event_id)

    if event and event.user_id == current_user.id:
        # If the event exists and belongs to the current user, delete it
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!', category='success')
    else:
        flash('Event not found or you do not have permission to delete it.', category='error')

    return redirect(url_for('views_creator.event'))
###########################################################################################################################################################################
@views_creator.route('/event_attendee_list', methods=['GET', 'POST'])
@login_required
def event_attendee_list():
    user_events = current_user.events
    events_data = []

    for event in user_events:
        event_data = json.loads(event.data1)
        
        # Ensure invited_attendees is parsed as JSON, assuming it's stored as a string in the database.
        attendee_data = json.loads(event.invited_attendees) if isinstance(event.invited_attendees, str) else event.invited_attendees

        # total_price = sum(thing.price for thing in new_things if thing.name in event_data)
        
        # Parse the rsvp_attendees field if it's stored as JSON
        rsvp_attendees = json.loads(event.rsvp_attendees) if event.rsvp_attendees else []
        
        # Load rejected invites for this event
        rejected_invites = []
        for attendee in attendee_data:
            # Make sure that each attendee is treated as a dictionary
            if isinstance(attendee, dict) and 'id' in attendee:
                attendee_event = Attendee_events5.query.filter_by(user_id=attendee['id']).first()
                if attendee_event and attendee_event.rejected_invites:
                    rejected_invites_json = json.loads(attendee_event.rejected_invites)
                    # Filter for this specific event's rejected invites
                    rejected_for_event = [reject for reject in rejected_invites_json if reject['event_name'] == event.event_name]
                    rejected_invites.extend(rejected_for_event)
            else:
                print(f"Unexpected attendee data structure: {attendee}")

        events_data.append({
            'event_name': event.event_name,
            'event_desc': event.event_desc,
            'data1': event_data,
            'id': event.id,
            'rsvp_attendees': rsvp_attendees,  # Decoded RSVP attendees
            'invited_attendees': attendee_data,
            'rejected_invites': rejected_invites,  # Add rejected invite details
            'max_attendee_num': event.max_attendee_num,
            'start_date': event.start_date,
            'end_date': event.end_date
        })

    return render_template('event_attendee_list.html', user=current_user, name=current_user.first_name, events=events_data)
###########################################################################################################################################################################
@views_creator.route('/create_event_history')
@login_required
def create_event_history():
    # Query all records created by the current user
    event_history = Event_records2.query.filter_by(creator_id=current_user.id).all()

    return render_template('create_event_history.html', user=current_user, name=current_user.first_name, event_history=event_history)