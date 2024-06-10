"""
Heart Rate Producer

Name: Topaz Montague

Date: 6.10.2024

File Description & Approach:
This Python script reads heart rate data from a CSV file and sends it to three RabbitMQ task queues, 
simulating real-time heart rate readings from a wearable device. It establishes a RabbitMQ connection, 
clears any existing messages in the queues, and declares durable queues for message persistence. 
The script iterates through the CSV file, converts heart rate readings to floats, formats them as messages, 
and publishes them to the respective queues with a 30-second delay between readings. 
Error handling ensures graceful exit if the RabbitMQ connection fails, and the connection is closed after processing.
"""

import csv
import pika
import sys
import time
import webbrowser

# Declare variables
heart_rate_monitor_queue = "01-heart-rate-monitor"
heart_rate_drop_queue = "02-heart-rate-drop"
heart_rate_stall_queue = "03-heart-rate-stall"
heart_rate_elevated_queue = "04-heart-rate-elevated"
csv_file = 'heart_rate.csv'

def offer_rabbitmq_admin_site(show_offer):
    """Offer to open the RabbitMQ Admin website."""
    if show_offer == "True":
        ans = input("Would you like to monitor RabbitMQ queues? y or n ")
        print()
        if ans.lower() == "y":
            webbrowser.open_new("http://localhost:15672/#/queues")
            print()
    else:
        webbrowser.open_new("http://localhost:15672/#/queues")
        print()

def main(host: str, csv_file: str):
    """
    Creates and sends a message to the queue each execution.
    This process runs and finishes.

    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
        csv_file (str): the CSV file to read data from
    """
    try:
        # Read CSV file
        with open(csv_file, 'r') as file:
            reader = csv.reader(file, delimiter=',')
            # Skip header
            header = next(reader)

            try:
                # Create a blocking connection to the RabbitMQ server
                conn = pika.BlockingConnection(pika.ConnectionParameters(host))
                # Use the connection to create a communication channel
                ch = conn.channel()

                # Clear queues to clear out old messages
                ch.queue_delete(heart_rate_monitor_queue)
                ch.queue_delete(heart_rate_drop_queue)
                ch.queue_delete(heart_rate_stall_queue)
                ch.queue_delete(heart_rate_elevated_queue)

                # Declare durable queues
                ch.queue_declare(heart_rate_monitor_queue, durable=True)
                ch.queue_declare(heart_rate_drop_queue, durable=True)
                ch.queue_declare(heart_rate_stall_queue, durable=True)
                ch.queue_declare(heart_rate_elevated_queue, durable=True)

                for row in reader:
                    time_stamp, heart_rate = row

                    # Convert numbers to floats and send messages to respective queues
                    try:
                        heart_rate_value = float(heart_rate)
                        heart_rate_message = f"{time_stamp}, {heart_rate_value}".encode()
                        ch.basic_publish(exchange="", routing_key=heart_rate_monitor_queue, body=heart_rate_message)
                        print(f" [x] Sent {heart_rate_message} on {heart_rate_monitor_queue}")
                        
                        # Send the same message to specific queues for individual monitoring tasks
                        ch.basic_publish(exchange="", routing_key=heart_rate_drop_queue, body=heart_rate_message)
                        print(f" [x] Sent {heart_rate_message} on {heart_rate_drop_queue}")
                        
                        ch.basic_publish(exchange="", routing_key=heart_rate_stall_queue, body=heart_rate_message)
                        print(f" [x] Sent {heart_rate_message} on {heart_rate_stall_queue}")
                        
                        ch.basic_publish(exchange="", routing_key=heart_rate_elevated_queue, body=heart_rate_message)
                        print(f" [x] Sent {heart_rate_message} on {heart_rate_elevated_queue}")
                    except ValueError:
                        pass

                    # Read values every 30 seconds
                    time.sleep(30)

            except pika.exceptions.AMQPConnectionError as e:
                print(f"Error: Connection to RabbitMQ server failed: {e}")
                sys.exit(30)
            finally:
                # Close the connection to the server
                conn.close()

    except FileNotFoundError as e:
        print(f"Error: CSV file not found: {e}")
        sys.exit(30)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(30)

# Standard Python idiom to indicate main program entry point
# This allows us to import this module and use its functions without executing the code below.
if __name__ == "__main__":
    offer_rabbitmq_admin_site("False")
    main("localhost", csv_file)
