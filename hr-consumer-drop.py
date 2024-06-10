"""
Heart Rate Drop Consumer

Name: Topaz Montague

Date: 6.10.2024

File Description & Approach:
This Python script monitors heart rate data for significant drops by reading messages from a RabbitMQ queue 
and using a deque to track the five most recent readings. If the heart rate decreases by 15 bpm or more within 2.5 minutes, 
an email alert is sent using SMTP, with configurations read from a TOML file. 
The script establishes a RabbitMQ connection, manages the queue, processes messages with a callback function, 
and includes robust error handling. It is designed for both direct execution and module importation, 
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
heart_rate_drop_queue = "02-heart-rate-drop"
drop_deque = deque(maxlen=5)  # limited to 5 items (the 5 most recent readings)
drop_subject = "HEART RATE DROP ALERT"
drop_content = "HEART RATE DROP ALERT: Heart rate has decreased by 15 bpm or more in the last 2.5 minutes."

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

def drop_callback(ch, method, properties, body):
    """Define behavior on getting a message about the heart rate drop."""

    message = body.decode().split(",")
    time_stamp = message[0]
    heart_rate = float(message[1])

    # Add the heart rate to the deque
    drop_deque.append(heart_rate)

    # Check for heart rate drop
    if len(drop_deque) == drop_deque.maxlen:
        drop_change = drop_deque[-1] - drop_deque[0]
        if drop_change <= -15:
            print(f"HEART RATE DROP ALERT: Current heart rate is: {heart_rate}, change in last 2.5 minutes: {drop_change} bpm")
            create_and_send_email_alert(drop_subject, drop_content)

    print(f"Current heart rate is: {heart_rate}")

    # Acknowledge the message was received and processed
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main(hn: str = "localhost", qn: str = "heart_rate_drop_queue"):
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
        channel.queue_delete(heart_rate_drop_queue)
        # Use the channel to declare a durable queue
        channel.queue_declare(heart_rate_drop_queue, durable=True)
        # Set the prefetch count to one to limit the number of messages being consumed and processed concurrently
        channel.basic_qos(prefetch_count=1)
        # Configure the channel to listen on a specific queue and use the drop_callback function
        channel.basic_consume(heart_rate_drop_queue, auto_ack=False, on_message_callback=drop_callback)
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
    main("localhost", "heart_rate_drop_queue")
