# streaming-07-custom-project
Project 7 repository for custom streaming project - Heart Rate Monitor

# Author: Topaz Montague

# Project Repository
[Custom Project - Heart Rate Monitor Program](https://github.com/tfmontague/streaming-06-smart-smoker)

# Heart Rate Monitor Program

## Project Overview
This project is to design and implement a Heart Rate Monitor program that continuously tracks and analyzes heart rate data.

The Heart Rate Monitor program processes a CSV file to set up a producer with three task queues. It simulates continuous heart rate readings from a wearable device, capturing readings every 30 seconds.

The `heart_rate.csv` file includes two columns: 

| Date-time stamp | Heart rate |
|-----------------|------------|

Three consumers are assigned to the producer, each one dedicated to a specific heart rate monitoring task.

## Project Approach
Python will be used to:
- Simulate a streaming series of heart rate readings from a wearable device.
- Create a producer to send these heart rate readings to RabbitMQ.
- Create three consumer processes, each one monitoring one of the heart rate streams.
- Perform calculations to determine if a significant event has occurred.

## Program Significant Events & Alerts
The Heart Rate Monitor program is designed to be triggered based on the following events:
- **Heart Rate Drop Alert!** Heart rate decreases by more than 15 beats per minute (bpm) in 2.5 minutes.
- **Heart Rate Stall!** Heart rate changes less than 1 bpm in 10 minutes.
- **Heart Rate Elevated!** Heart rate increases by more than 20 bpm in 2 minutes.

And to signal the following based on the events:
- Alert the user when a significant event occurs.
- Send the user an email for each alert.

## Program Specifications

### Time Windows
- Heart rate drop time window is 2.5 minutes.
- Heart rate stall time window is 10 minutes.
- Heart rate elevated time window is 2 minutes.

### Deque Max Length
- At one reading every 1/2 minute, the heart rate drop deque max length is 5 (2.5 min * 1 reading/0.5 min).
- At one reading every 1/2 minute, the heart rate stall deque max length is 20 (10 min * 1 reading/0.5 min).
- At one reading every 1/2 minute, the heart rate elevated deque max length is 4 (2 min * 1 reading/0.5 min).

### Condition To Monitor
- If heart rate decreases by 15 bpm or more in 2.5 min (or 5 readings) --> heart rate drop alert!
- If heart rate change is 1 bpm or less in 10 min (or 20 readings) --> heart rate stall alert!
- If heart rate increases by 20 bpm or more in 2 min (or 4 readings) --> heart rate elevated alert!

## Prerequisites
- RabbitMQ server running.
- Pika installed in the active Python environment.
- Configure `.env.toml` with appropriate email configuration settings:
  
```python
  outgoing_email_host = "smtp.example.com"
  outgoing_email_port = XXX
  outgoing_email_address = "your_email@example.com"
  outgoing_email_password = "your_password"
```

## Running the Program
- Open VS Code Terminal.
- Open 3 additional VS Code Terminals using the Split Terminal function.
- Run `python hr-producer.py` in the 1st terminal.
- Run `python hr-consumer-monitor.py` in the 2nd terminal.
- Run `python hr-consumer-drop.py` in the 3rd terminal.
- Run `python hr-consumer-stall.py` in the 4th terminal.
- Run `python hr-consumer-elevated.py` in the 5th terminal.

## Screenshots
- Multiple Concurrent Processes
![alt text](<Screenshot 2024-06-10 165651.png>)

- Significant Events
![alt text](<Screenshot 2024-06-10 170915.png>)
![alt text](<Screenshot 2024-06-10 170702.png>)
![alt text](<Screenshot 2024-06-10 170422.png>)

- Email Alerts
![alt text](<Screenshot 2024-06-10 171055.png>)
![alt text](<Screenshot 2024-06-10 171123.png>)