"""
Heart Rate Monitor Consumer

Name: Topaz Montague

Date: 6.10.2024

File Description & Approach:
This Python script monitors heart rate data by reading messages from a RabbitMQ queue 
and using a deque to track the most recent readings. It checks for significant changes 
in heart rate (drops, stalls, or elevations) within specific time windows, and sends 
an email alert using SMTP if any condition is met. The script establishes a RabbitMQ 
connection, manages the queue, processes messages with a callback function, and includes 
robust error handling. It is designed for both direct execution and module importation, 
requiring Python 3.11 for TOML support.

"""
from collections import deque
from email.message import EmailMessage
import pika
import pprint
import smtplib
import sys
import tomllib  # requires Python 3.11

# Declare variables
heart_rate_monitor_queue = "01-heart-rate-monitor"
heart_rate_drop_queue = "02-heart-rate-drop"
heart_rate_stall_queue = "03-heart-rate-stall"
heart_rate_elevated_queue = "04-heart-rate-elevated"
drop_deque = deque(maxlen=5)  # limited to 5 items (the 5 most recent readings)
stall_deque = deque(maxlen=20)  # limited to 20 items (the 20 most recent readings)
elevated_deque = deque(maxlen=4)  # limited to 4 items (the 4 most recent readings)

# Email subjects and contents
drop_subject = "HEART RATE DROP ALERT"
drop_content = "HEART RATE DROP ALERT: Heart rate has decreased by 15 bpm or more in the last 2.5 minutes."

stall_subject = "HEART RATE STALL ALERT"
stall_content = "HEART RATE STALL ALERT: Heart rate change is less than 1 bpm in the last 10 minutes."

elevated_subject = "HEART RATE ELEVATED ALERT"
elevated_content = "HEART RATE ELEVATED ALERT: Heart rate has increased by 20 bpm or more in the last 2 minutes."

def create_and_send_email_alert(email_subject: str, email_body: str):
    """Read outgoing email info from a TOML config file"""

    with open(".env.toml", "rb") as file_object:
        secret_dict = tomllib.load(file_object)
    pprint.pprint(secret_dict)

    # Basic information
    host = secret_dict["outgoing_email_host"]
    port = secret_dict["outgoing_email_port"]
    outemail = secret_dict["outgoing_email_address"]
    outpwd = secret_dict["outgoing_email_password"]

    # Create an instance of an EmailMessage
    msg = EmailMessage()
    msg["From"] = outemail
    msg["To"] = outemail
    msg["Reply-to"] = outemail
    msg["Subject"] = email_subject
    msg.set_content(email_body)

    print("========================================")
    print(f"Prepared Email Message: ")
    print("========================================")
    print()
    print(f"{str(msg)}")
    print("========================================")
    print()

    try:
        if port == 465:
            # Use SMTP_SSL for port 465
            server = smtplib.SMTP_SSL(host, port)
        else:
            # Use SMTP for port 587
            server = smtplib.SMTP(host, port)
            server.starttls()

        server.set_debuglevel(2)

        print("========================================")
        print(f"SMTP server created: {str(server)}")
        print("========================================")
        print()

        server.login(outemail, outpwd)
        print("========================================")
        print(f"Successfully logged in as {outemail}.")
        print("========================================")
        print()

        server.send_message(msg)
        print("========================================")
        print(f"Message sent.")
        print("========================================")
        print()
    except Exception as e:
        print(f"Failed to connect or send email: {e}")
    finally:
        server.quit()
        print("========================================")
        print(f"Session terminated.")
        print("========================================")

def monitor_callback(ch, method, properties, body):
    """Define behavior on getting a message about the heart rate."""

    message = body.decode().split(",")
    time_stamp = message[0]
    heart_rate = float(message[1])

    # Add the heart rate to all deques
    drop_deque.append(heart_rate)
    stall_deque.append(heart_rate)
    elevated_deque.append(heart_rate)

    # Check for heart rate drop
    if len(drop_deque) == drop_deque.maxlen:
        drop_change = drop_deque[-1] - drop_deque[0]
        if drop_change <= -15:
            print(f"HEART RATE DROP ALERT: Current heart rate is: {heart_rate}, change in last 2.5 minutes: {drop_change} bpm")
            create_and_send_email_alert(drop_subject, drop_content)

    # Check for heart rate stall
    if len(stall_deque) == stall_deque.maxlen:
        stall_change = max(stall_deque) - min(stall_deque)
        if stall_change < 1:
            print(f"HEART RATE STALL ALERT: Current heart rate is: {heart_rate}, change in last 10 minutes: {stall_change} bpm")
            create_and_send_email_alert(stall_subject, stall_content)

    # Check for heart rate elevated
    if len(elevated_deque) == elevated_deque.maxlen:
        elevated_change = elevated_deque[-1] - elevated_deque[0]
        if elevated_change >= 20:
            print(f"HEART RATE ELEVATED ALERT: Current heart rate is: {heart_rate}, change in last 2 minutes: {elevated_change} bpm")
            create_and_send_email_alert(elevated_subject, elevated_content)

    print(f"Current heart rate is: {heart_rate}")

    # Acknowledge the message was received and processed
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main(hn: str = "localhost", qn: str = "task_queue"):
    """ Continuously listen for task messages on a named queue.
    
    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
        qn (str): queue name
    """
    try:
        # Try this code, if it works, keep going
        # Create a blocking connection to the RabbitMQ server
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=hn))
    except Exception as e:
        print()
        print("ERROR: connection to RabbitMQ server failed.")
        print(f"Verify the server is running on host={hn}.")
        print(f"The error says: {e}")
        print()
        sys.exit(1)

    try:
        # Use the connection to create a communication channel
        channel = connection.channel()
        # Use the channel to clear the queue
        channel.queue_delete(heart_rate_monitor_queue)
        channel.queue_delete(heart_rate_drop_queue)
        channel.queue_delete(heart_rate_stall_queue)
        channel.queue_delete(heart_rate_elevated_queue)
        # Use the channel to declare durable queues
        channel.queue_declare(heart_rate_monitor_queue, durable=True)
        channel.queue_declare(heart_rate_drop_queue, durable=True)
        channel.queue_declare(heart_rate_stall_queue, durable=True)
        channel.queue_declare(heart_rate_elevated_queue, durable=True)
        # Set the prefetch count to one to limit the number of messages being consumed and processed concurrently
        channel.basic_qos(prefetch_count=1)
        # Configure the channel to listen on a specific queue and use the monitor_callback function
        channel.basic_consume(heart_rate_monitor_queue, auto_ack=False, on_message_callback=monitor_callback)
        # Print a message to the console for the user
        print(" [*] Ready for work. To exit press CTRL+C")
        # Start consuming messages via the communication channel
        channel.start_consuming()
    except Exception as e:
        print()
        print("ERROR: something went wrong.")
        print(f"The error says: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print(" User interrupted continuous listening process.")
        sys.exit(0)
    finally:
        print("\nClosing connection. Goodbye.\n")
        connection.close()

if __name__ == "__main__":
    main("localhost", "heart_rate_monitor_queue")
