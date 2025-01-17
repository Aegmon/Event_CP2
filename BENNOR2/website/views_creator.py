from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from .models import Events16, Users9, Attendee_events8, Client_events7, Event_records7, Client_Attend_Events2, Client_Hired_Suppliers5, SupplierRating3
from . import db, socketio
from .gen_algo_final import *
import json, random, csv
from flask_socketio import join_room, leave_room, send, SocketIO, emit
from datetime import datetime
from string import ascii_uppercase

views_creator = Blueprint('views_creator', __name__)

rooms = {}

########################################################################################################################################################################### Event Creator Video Chat

@views_creator.route("/video_chat_dashboard", methods=["POST", "GET"])
@login_required
def video_chat_dashboard():
    return render_template("video_chat_dashboard.html", user=current_user, role=current_user.role, first_name=current_user.first_name, last_name=current_user.last_name)

@views_creator.route("/video_create_meeting", methods=["POST", "GET"])
@login_required
def video_create_meeting():
    return render_template("video_create_meeting.html", user=current_user, role=current_user.role, first_name=current_user.first_name, last_name=current_user.last_name)

@views_creator.route("/video_join_meeting", methods=["POST", "GET"])
@login_required
def video_join_meeting():
    if request.method == "POST":
        room_id = request.form.get("roomID")
        return redirect(f"/video_create_meeting?roomID={room_id}")
    return render_template("video_join_meeting.html", user=current_user, role=current_user.role, first_name=current_user.first_name, last_name=current_user.last_name)

########################################################################################################################################################################### Event Creater Live Chat
def generate_unique_code(length=5):
    """Generates a unique room code."""
    while True:
        code = ''.join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            rooms[code] = {"messages": [], "members": 0}  # Initialize room structure
            return code

@views_creator.route("/join_room", methods=["POST", "GET"])
@login_required
def join_room_view():
    """Page where users enter the room code to join."""
    session.clear()

    # Fetch events created by the current user
    created_events = Events16.query.filter_by(user_id=current_user.id).all()
    client_attend = Client_Attend_Events2.query.filter_by(client_id=current_user.id).all()

    if request.method == "POST":
        code = request.form.get("code")
        if not code:
            return render_template("join_room.html", error="Please enter a room code.", user=current_user, role=current_user.role, created_events=created_events, client_attend=client_attend)

        if code not in rooms:
            return render_template("join_room.html", error="Room does not exist.", user=current_user, role=current_user.role, created_events=created_events, client_attend=client_attend)

        session["room"] = code
        session["name"] = current_user.role + " : " + current_user.first_name  # Use the user's first name
        return redirect(url_for('views_creator.room'))

    return render_template("join_room.html", user=current_user, role=current_user.role, created_events=created_events, client_attend=client_attend)

@views_creator.route("/room")
@login_required
def room():
    """Chat room view."""
    room_code = session.get("room")
    if room_code is None or room_code not in rooms:
        return redirect(url_for("views_creator.join_room_view"))
    
    # Retrieve the event associated with this room code
    event = Events16.query.filter_by(room_code=room_code).first()
    if not event:
        flash("No event found for this room.")
        return redirect(url_for("views_creator.join_room_view"))
    
    event_name = event.event_name  # Get the event name
    creator = Users9.query.filter_by(id=event.user_id).first()  # Get event creator's name
    creator_name = f"{creator.first_name} {creator.last_name}"

    return render_template("room.html", user=current_user, code=room_code, event_name=event_name, creator_name=creator_name, messages=rooms[room_code]["messages"], role=current_user.role)

@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    if room not in rooms:
        return 

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    rooms[room]["messages"].append(content)  # Store message in the room
    send(content, to=room)  # Emit message to room
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    
    if room not in rooms:
        return  # Ignore if room does not exist
    
    join_room(room)
    rooms[room]["members"] += 1
    send({"name": name, "message": "has entered the room"}, to=room)
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        send({"name": name, "message": "has left the room"}, to=room)
        print(f"{name} has left the room {room}")

########################################################################################################################################################################### Event Creator Home

@views_creator.route('/create_event_profile')
@login_required
def create_event_profile():
    # Get the current user
    user = current_user

    # Pass the user data and images to the template
    return render_template('create_event_profile.html', user=user)

###########################################################################################################################################################################

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
        budget = request.form.get('budget')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        max_attendee_num_str = request.form.get('max_attendee_num')
        selected_attendees = request.form.getlist('attendees')

        # Generate a unique room code for the chat room
        room_code = generate_unique_code()
        session["room"] = room_code
        session["name"] = current_user.role + " : " + current_user.first_name  # Or however you want to set the name

        # Save the room to persist chats
        rooms[room_code] = {"members": 0, "messages": []}

        try:
            budget = int(budget)
            if budget < 20000:
                flash('Budget must be at least 20000 Pesos.', category='error')
                return redirect(request.url)
        except ValueError:
            flash('Budget must be a valid whole number (no decimals).', category='error')
            return redirect(request.url)

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
            attendee = Users9.query.get(attendee_id)
            if attendee:
                attendee_details.append({
                    'id': attendee.id,
                    'name': attendee.first_name,
                    'lname': attendee.last_name,
                    'email': attendee.email
                })

        # Convert selected attendee details to JSON
        invited_attendees_json = json.dumps(attendee_details)

        # Run Algo Here
        total_price = sum(thing.price for thing in things_list3)
        max_price_limit = float(budget)  # Set to your desired maximum price
        price_limit = min(total_price, max_price_limit)

        fitness_limit = 1000
        population_size = 20
        generation_limit = 100  

        best_genome, generations = run_evolution(
        populate_func=partial(generate_population, size=population_size),
        fitness_func=partial(fitness, price_limit=price_limit),
        fitness_limit=fitness_limit,
        generation_limit=generation_limit
        )

        best_answers = genome_to_things(best_genome, price_limit)

        # Convert the list of best answers to JSON
        answers_json = json.dumps(best_answers)

        # Create new event instance and save it to the database
        new_event = Events16(
            event_name=event_name,
            event_desc=event_desc,
            room_code=room_code,
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

        flash('Event added!', category='success')
        # Now store this event in each selected attendee's Attendee_events8 "invites" field
        for attendee_id in selected_attendees:
            attendee = Users9.query.get(attendee_id)
            if attendee:
                # Get or create the Attendee_events8 entry for this user
                attendee_event = Attendee_events8.query.filter_by(user_id=attendee.id).first()
                if not attendee_event:
                    attendee_event = Attendee_events8(user_id=attendee.id, invites='[]')
                    db.session.add(attendee_event)
                
                # Load the current invites
                invites = json.loads(attendee_event.invites)

                # Add the new event to the invites list
                invites.append({
                    'event_name': event_name,
                    'event_desc': event_desc,
                    'event_privacy': event_privacy,
                    'start_date': start_date.strftime('%Y-%m-%d %H:%M'),
                    'end_date': end_date.strftime('%Y-%m-%d %H:%M'),
                    'creator_name': current_user.first_name + ' ' + current_user.last_name  # Add the event creator's name
                })

                # Save back the updated invites list
                attendee_event.invites = json.dumps(invites)

        db.session.commit()

        flash('Event added and invites sent!', category='success')
        return redirect(url_for('views_creator.created_event_edit'))

        # Query all attendees with the role 'Attendee'
    attendees = Users9.query.filter_by(role='Attendee').all()

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
            'room_code': event.room_code,
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
    event = Events16.query.get(event_id)

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
    event = Events16.query.filter_by(id=event_id, user_id=current_user.id).first()

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
    event = Events16.query.get(event_id)

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
        try:
            # Load and parse event data
            event_data = json.loads(event.data1) if event.data1 else {}
        except (TypeError, json.JSONDecodeError):
            event_data = {}  # Handle invalid or missing JSON
            print(f"Failed to parse event data1 for event ID {event.id}")

        try:
            # Ensure invited_attendees is parsed as JSON, assuming it's stored as a string in the database
            attendee_data = json.loads(event.invited_attendees) if isinstance(event.invited_attendees, str) else event.invited_attendees or []
        except (TypeError, json.JSONDecodeError):
            attendee_data = []
            print(f"Failed to parse invited_attendees for event ID {event.id}")
        
        try:
            # Parse the rsvp_attendees field if it's stored as JSON
            rsvp_attendees = json.loads(event.rsvp_attendees) if event.rsvp_attendees else []
        except (TypeError, json.JSONDecodeError):
            rsvp_attendees = []
            print(f"Failed to parse rsvp_attendees for event ID {event.id}")

        # Load rejected invites for this event
        rejected_invites = []
        for attendee in attendee_data:
            try:
                # Make sure that each attendee is treated as a dictionary
                if isinstance(attendee, dict) and 'id' in attendee:
                    attendee_event = Attendee_events8.query.filter_by(user_id=attendee['id']).first()
                    if attendee_event and attendee_event.rejected_invites:
                        rejected_invites_json = json.loads(attendee_event.rejected_invites)
                        # Filter for this specific event's rejected invites
                        rejected_for_event = [reject for reject in rejected_invites_json if reject['event_name'] == event.event_name]
                        rejected_invites.extend(rejected_for_event)
                else:
                    print(f"Unexpected attendee data structure: {attendee}")
            except Exception as e:
                print(f"Error processing attendee data: {e}")

        # Append event data to list
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

@views_creator.route('/create_event_history', methods=['GET', 'POST'])
@login_required
def create_event_history():
    # Fetch all event records created by the current user
    event_history = Event_records7.query.filter_by(creator_id=current_user.id).all()

    for event in event_history:
        if event.data1:
            try:
                supplier_names = json.loads(event.data1)
                event.supplier_names = []
                if event.supplier_hired_status:
                    hire_status = json.loads(event.supplier_hired_status)
                else:
                    hire_status = {}

                for name in supplier_names:
                    matched_supplier = next((thing for thing in new_things3 if thing.name == name), None)
                    if matched_supplier:
                        event.supplier_names.append({
                            'name': matched_supplier.name,
                            'business_name': matched_supplier.business_name,
                            'contact_number': matched_supplier.contact_number,
                            'email': matched_supplier.email,
                            'rating': matched_supplier.rating,
                            'price': matched_supplier.price,
                            'hired': hire_status.get(matched_supplier.name, False)  # Add hire status here
                        })
            except json.JSONDecodeError:
                event.supplier_names = []
        else:
            event.supplier_names = []

    return render_template('create_event_history.html', user=current_user, event_history=event_history, name=current_user.first_name)

@views_creator.route('/delete_event_record/<int:event_id>', methods=['POST'])
@login_required
def delete_event_record(event_id):
    # Find the event by ID
    event_to_delete = Event_records7.query.filter_by(id=event_id, creator_id=current_user.id).first()

    if event_to_delete:
        # Delete the event from the database
        db.session.delete(event_to_delete)
        db.session.commit()
        flash('Event successfully deleted', 'success')
    else:
        flash('Event not found or you do not have permission to delete it', 'error')

    # Redirect back to the event history page
    return redirect(url_for('views_creator.create_event_history'))

@views_creator.route('/toggle_hire_status/<int:event_id>/<string:supplier_name>', methods=['POST'])
@login_required
def toggle_hire_status(event_id, supplier_name):
    event = Event_records7.query.get(event_id)

    if event:
        # Initialize supplier_hired_status if it doesn't exist
        if not event.supplier_hired_status:
            event.supplier_hired_status = json.dumps({})

        # Load the current supplier hire status
        hire_status = json.loads(event.supplier_hired_status)

        # Toggle the status of the supplier
        if supplier_name in hire_status:
            hire_status[supplier_name] = not hire_status[supplier_name]
        else:
            hire_status[supplier_name] = True

        # Save the updated status back to the event record
        event.supplier_hired_status = json.dumps(hire_status)
        db.session.commit()

        return jsonify({'status': hire_status[supplier_name]})
    
    return jsonify({'error': 'Event not found'}), 404

###########################################################################################################################################################################

@views_creator.route('/create_record/<int:event_id>', methods=['POST'])
@login_required
def create_record(event_id):
    # Fetch the specific event by ID
    event = Events16.query.get(event_id)
    
    if not event:
        flash('Event not found', category='error')
        return redirect(url_for('views_creator.created_event_edit'))

    # Check if the event has already been finalized (exists in Event_records7)
    existing_record = Event_records7.query.filter_by(creator_id=current_user.id, event_name=event.event_name).first()

    if existing_record:
        flash('This event has already been finalized and saved to history.', category='warning')
        return redirect(url_for('views_creator.created_event_edit'))

    # Extract event details
    event_name = event.event_name
    event_desc = event.event_desc
    event_type = event.event_type
    event_privacy = event.event_privacy
    start_date = event.start_date
    end_date = event.end_date
    room_code = event.room_code
    data1 = event.data1  # Assuming this contains a JSON string of supplier names
    total_price = request.form.get('total_price', type=float)

    # Create a new Event_records7 entry
    new_event_record = Event_records7(
        event_name=event_name,
        event_desc=event_desc,
        event_type=event_type,
        event_privacy=event_privacy,
        data1=data1,
        room_code=room_code,
        creator_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        total_cost=total_price  # Save the total cost
    )
    
    try:
        # Add the new record to the database
        db.session.add(new_event_record)
        db.session.commit()
        flash('Event has been successfully saved to history!', category='success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving event: {e}", category='error')

    # Redirect to the event history page
    return redirect(url_for('views_creator.create_event_history'))

########################################################################################################################################################################### Client
########################################################################################################################################################################### Client

@views_creator.route('/create_event_profile_client')
@login_required
def create_event_profile_client():
    # Get the current user
    user = current_user

    # Pass the user data and images to the template
    return render_template('create_event_profile.html', user=user)
########################################################################################################################################################################### 

@views_creator.route('/client_home', methods=['GET', 'POST'])
@login_required
def client_home():
    return render_template('client_home.html', user=current_user, name=current_user.first_name)

@views_creator.route('/client', methods=['GET', 'POST'])
@login_required
def client():
    if request.method == 'POST':
        # Get form inputs
        event_name = request.form.get('event_name')
        event_desc = request.form.get('event_desc')
        event_type = request.form.get('event_type')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        budget = request.form.get('budget')
        max_attendee_num_str = request.form.get('max_attendee_num')

        # Check if any of the required fields are empty
        if not event_name or not event_desc or not start_date_str or not end_date_str or not budget or not max_attendee_num_str or not event_type:
            flash('Please fill out all fields.', category='error')
            return redirect(request.url)

        # Validate budget
        try:
            budget = int(budget)
            if budget < 20000:
                flash('Budget must be at least 20000 Pesos.', category='error')
                return redirect(request.url)
        except ValueError:
            flash('Budget must be a valid whole number (no decimals).', category='error')
            return redirect(request.url)

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

        # Validate that end date is not before start date
        if end_date < start_date:
            flash('End date cannot be before the start date.', category='error')
            return redirect(request.url)

        # Run Algo Here
        total_price = sum(thing.price for thing in things_list3)
        max_price_limit = float(budget)  # Set to your desired maximum price
        price_limit = min(total_price, max_price_limit)

        fitness_limit = 1000
        population_size = 20
        generation_limit = 100  

        best_genome, generations = run_evolution(
        populate_func=partial(generate_population, size=population_size),
        fitness_func=partial(fitness, price_limit=price_limit),
        fitness_limit=fitness_limit,
        generation_limit=generation_limit
        )

        best_answers = genome_to_things(best_genome, price_limit)

        # Convert the list of best answers to JSON
        answers_json = json.dumps(best_answers)

        # Create new event instance and save it to the database
        new_event = Client_events7(
            event_name=event_name,
            event_desc=event_desc,
            event_type=event_type,  # Save event status
            data1=answers_json,
            user_id=current_user.id,
            max_attendee_num=max_attendee_num,
            start_date=start_date,
            end_date=end_date,  # Save the selected attendees as JSON
        )
        db.session.add(new_event)
        db.session.commit()

        flash('Client event added!', category='success')
    
    return render_template("client.html", user=current_user, name=current_user.first_name)

###########################################################################################################################################################################

@views_creator.route('/client_events', methods=['POST', 'GET'])
def client_events():
    user_events = current_user.client_events
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
            'data1': event_data,
            'id': event.id,
            'total_price': total_price,
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

    return render_template("client_events.html", user=current_user, name=current_user.first_name, client_events=events_data, cake1=cake1, 
                                                    digital_printing1=digital_printing1, event_planner1=event_planner1, 
                                                    grazing_table1=grazing_table1, makeup_and_hair1=makeup_and_hair1, 
                                                    photobooth1=photobooth1, photographer1=photographer1, catering1=catering1, 
                                                    church1=church1, event_stylist1=event_stylist1, events_place1=events_place1, 
                                                    lights_and_sounds1=lights_and_sounds1)

###########################################################################################################################################################################

@views_creator.route('/delete_supplier', methods=['POST'])
@login_required
def delete_supplier():
    data = request.get_json()  # Get the JSON data from the request
    event_id = data.get('event_id')
    supplier_name = data.get('supplier_name')

    # Fetch the event by ID
    event = Client_events7.query.filter_by(id=event_id, user_id=current_user.id).first()

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

@views_creator.route('/client_delete_event', methods=['POST'])
@login_required
def client_delete_event():
    data = request.get_json()
    event_id = data.get('event_id')

    # Fetch the event by ID
    event = Client_events7.query.filter_by(id=event_id, user_id=current_user.id).first()

    if not event:
        return jsonify({'success': False, 'message': 'Event not found'}), 404

    # Delete the event from the database
    db.session.delete(event)
    db.session.commit()

    return jsonify({'success': True})

###########################################################################################################################################################################

@views_creator.route('/client_hire_supplier', methods=['POST', 'GET'])
@login_required
def client_hire_supplier():
    # Rendering the supplier list for GET request
    return render_template(
        "client_hire_supplier.html", user=current_user, name=current_user.first_name, new_things3=new_things3)

@views_creator.route('/hire_supplier', methods=['POST'])
@login_required
def hire_supplier():
    supplier_name = request.form.get('supplier_name')
    supplier_business_name = request.form.get('supplier_business_name')
    supplier_contact_number = request.form.get('supplier_contact_number')
    supplier_email = request.form.get('supplier_email')
    supplier_type = request.form.get('supplier_type')
    supplier_price = request.form.get('supplier_price')
    supplier_rating = request.form.get('supplier_rating')

    # Create a new Client_Hired_Suppliers5 record
    new_hired_supplier = Client_Hired_Suppliers5(
        client_id=current_user.id,
        supplier_name=supplier_name,
        supplier_business_name=supplier_business_name,
        supplier_contact_number=supplier_contact_number,
        supplier_email=supplier_email,
        supplier_type=supplier_type,
        supplier_price=supplier_price,
        supplier_rating=supplier_rating,
        hired_status=False
    )
    # Add to the database
    db.session.add(new_hired_supplier)
    db.session.commit()
    flash(f"Supplier {supplier_name} has been successfully hired!", category='success')

    return redirect(url_for('views_creator.client_hire_supplier'))

@views_creator.route('/client_suppliers_hired', methods=['GET'])
@login_required
def client_suppliers_hired():
    # Query the database to find all suppliers hired by the current user
    hired_suppliers = Client_Hired_Suppliers5.query.filter_by(client_id=current_user.id).all()
    
    # Render the HTML template and pass the hired suppliers data
    return render_template('client_suppliers_hired.html', user=current_user, hired_suppliers=hired_suppliers)

@views_creator.route('/toggle_hired_status/<string:supplier_name>', methods=['POST'])
@login_required
def toggle_hired_status(supplier_name):
    # Find the supplier in the database using the client's ID
    supplier = Client_Hired_Suppliers5.query.filter_by(client_id=current_user.id, supplier_name=supplier_name).first()
    if supplier:
        # Toggle the hired status
        supplier.hired_status = not supplier.hired_status
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False), 404

@views_creator.route('/client_attend_events', methods=['POST', 'GET'])
@login_required
def client_attend_events():
    # Fetch only public events
    public_events = Events16.query.filter_by(event_privacy="Public").all()
    events_data = []
    
    for event in public_events:
        # Get event creator's name from Users9 table
        creator = Users9.query.get(event.user_id)
        creator_name = f"{creator.first_name} {creator.last_name}" if creator else "Unknown"

        events_data.append({
            'event_name': event.event_name,
            'event_desc': event.event_desc,
            'creator_name': creator_name,
            'room_code': event.room_code,
            'start_date': event.start_date.strftime("%Y-%m-%d %H:%M"),
            'end_date': event.end_date.strftime("%Y-%m-%d %H:%M")
        })
    return render_template("client_attend_events.html", user=current_user, name=current_user.first_name, public_events=events_data)

@views_creator.route('/client_rsvped_events', methods=['POST'])
@login_required
def client_rsvped_events():
    event_name = request.form.get('event_name')
    creator_name = request.form.get('creator_name')
    
    # Fetch the event from the database
    event = Events16.query.filter_by(event_name=event_name).first()
    
    # Check if the event exists
    if not event:
        flash('Event not found.', category='error')
        return redirect(url_for('views_creator.client_attend_events2'))
    
    # Check if the user already RSVPed for the event
    already_rsvped = Client_Attend_Events2.query.filter_by(client_id=current_user.id, event_name=event_name).first()
    if already_rsvped:
        flash('You have already RSVPed for this event.', category='error')
        return redirect(url_for('views_creator.client_attend_events2'))

    # Check if the event has space available
    rsvp_attendees = event.rsvp_attendees.split(',') if event.rsvp_attendees else []
    if len(rsvp_attendees) >= event.max_attendee_num:
        flash('The event is already full.', category='error')
        return redirect(url_for('views_creator.client_attend_events2'))

    # Add the current user to the rsvp_attendees
    rsvp_attendees.append(current_user.email)
    event.rsvp_attendees = ','.join(rsvp_attendees)
    
    # Save the event details to Client_Attend_Events2 table
    new_rsvp = Client_Attend_Events2(
        event_name=event.event_name,
        event_desc=event.event_desc,
        room_code=event.room_code,
        start_date=event.start_date,
        end_date=event.end_date,
        creator_name=creator_name,
        client_id=current_user.id
    )
    db.session.add(new_rsvp)
    db.session.commit()
    
    flash('You have successfully RSVPed for the event.', category='success')
    return redirect(url_for('views_creator.client_attend_events2'))

@views_creator.route('/client_events_to_attend')
@login_required
def client_events_to_attend():
    # Fetch all events the current client has RSVPed to
    rsvped_events = Client_Attend_Events2.query.filter_by(client_id=current_user.id).all()
    
    events_data = []
    for event in rsvped_events:
        events_data.append({
            'event_name': event.event_name,
            'event_desc': event.event_desc,
            'creator_name': event.creator_name,
            'room_code': event.room_code,
            'start_date': event.start_date.strftime("%Y-%m-%d %H:%M"),
            'end_date': event.end_date.strftime("%Y-%m-%d %H:%M"),
            'date_rsvped': event.date_rsvped.strftime("%Y-%m-%d %H:%M")
        })
    
    return render_template("client_events_to_attend.html", user=current_user, name=current_user.first_name, rsvped_events=events_data)

@views_creator.route('/view_creator', methods=['POST'])
@login_required
def view_creator():
    # Get the creator's name from the form
    creator_name = request.form.get('creator_name')
    
    # Query the database to find the user by their name
    creator = Users9.query.filter(
        (Users9.first_name + " " + Users9.last_name) == creator_name
    ).first()

    if not creator:
        flash('Creator not found!', category='error')
        return redirect(url_for('views_attendee.attendee_invites'))

    # Render the creator details on a new page
    return render_template('attendee_creator_view.html', creator=creator, user=current_user)

@views_creator.route('/rating_and_feedback', methods=['GET','POST'])
@login_required
def rating_and_feedback():
    return render_template('rating_and_feedback.html', user=current_user, new_things3=new_things3, name=current_user.first_name, role=current_user.role)

@views_creator.route('/rate_supplier', methods=['POST'])
@login_required
def rate_supplier():
    supplier_name = request.form.get('supplier_name')  # Get the supplier name from the form
    specific_supplier = next((thing for thing in new_things3 if thing.name == supplier_name), None)  # Find the specific supplier

    if not specific_supplier:
        flash('Supplier not found!', 'danger')  # Handle the case where supplier is not found
        return redirect(url_for('views_creator.rating_and_feedback'))

    # Query the SupplierRating3 table to get all ratings for the specific supplier
    supplier_ratings = SupplierRating3.query.filter_by(supplier_name=supplier_name).all()

    return render_template('rate_supplier.html', user=current_user, supplier=specific_supplier, ratings=supplier_ratings, role=current_user.role, name=current_user.first_name)

@views_creator.route('/submit_supplier_rating', methods=['POST'])
@login_required
def submit_supplier_rating():
    supplier_name = request.form.get('supplier_name')
    rating = float(request.form.get('rating')) 
    feedback = request.form.get('feedback')
    reviewer_name = current_user.first_name + " " + current_user.last_name
    reviewer_role = current_user.role

    # Find all ratings associated with the supplier_name
    supplier_ratings = SupplierRating3.query.filter_by(supplier_name=supplier_name).all()

    # Check if the current user has rated this supplier before
    for rating_record in supplier_ratings:
        if rating_record.reviewer_name == reviewer_name:
            # Calculate days since last rating
            days_since_last_rating = (datetime.now() - rating_record.date_reviewed).days
            if days_since_last_rating < 30:
                flash(f'You can only rate the same supplier every 30 days. {30 - days_since_last_rating} days remaining.', 'error')
                return redirect(url_for('views_creator.rating_and_feedback'))

    # If no recent rating from this user exists, proceed with saving the rating
    new_rating = SupplierRating3(
        supplier_name=supplier_name,
        rating=rating,
        feedback=feedback,
        reviewer_name=reviewer_name,
        reviewer_role=reviewer_role
    )
    
    db.session.add(new_rating)
    db.session.commit()

    # Query for all ratings of this supplier again
    all_ratings = SupplierRating3.query.filter_by(supplier_name=supplier_name).all()
    
    # Calculate the new average rating
    total_ratings = sum(r.rating for r in all_ratings)
    average_rating = total_ratings / len(all_ratings) if all_ratings else 0

    # List of CSV file paths where the supplier's rating needs to be updated
    csv_files = [
        cake, digital_printing, event_planner, grazing_table, 
        makeup_and_Hair, photobooth, photographer, catering, 
        church, event_stylist, events_place, lights_and_sounds, csv_file_path3
    ]

    # Function to update the rating in each CSV file
    def update_csv_file(file_path, supplier_name, new_rating):
        temp_rows = []
        with open(file_path, mode='r', newline='') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            fieldnames = csv_reader.fieldnames
            for row in csv_reader:
                if row['name'] == supplier_name:
                    row['rating'] = new_rating  # Update the rating
                temp_rows.append(row)

        # Write the updated rows back to the CSV file
        with open(file_path, mode='w', newline='') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(temp_rows)

    # Update the rating in all relevant CSV files
    for csv_file in csv_files:
        update_csv_file(csv_file, supplier_name, average_rating)

    # Reload the CSV data in memory
    things_list3.clear()
    cake_arr.clear()
    digital_printing_arr.clear()
    event_planner_arr.clear()
    grazing_table_arr.clear()
    makeup_and_hair_arr.clear()
    photobooth_arr.clear()
    photographer_arr.clear()
    catering_arr.clear()
    church_arr.clear()
    event_stylist_arr.clear()
    events_place_arr.clear()
    lights_and_sounds_arr.clear()

    # Re-read CSV files
    read_csv3(csv_file_path3, things_list3)
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

    if current_user.role == "Client":
        return redirect(url_for('views_creator.client_events'))

    flash('Rating and feedback submitted successfully!', 'success')
    return redirect(url_for('views_creator.rating_and_feedback'))