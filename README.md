# Palm-Vein-Payment
Due to the absence of actual palm vein scanning hardware, the authentication process is simulated using a palm image dataset obtained from Kaggle.

The system implementation focuses on two main modules:
Palm Vein Authentication Module

This module performs the following tasks:
• Image preprocessing
• Feature extraction using ORB algorithm
• Feature matching for authentication
• Verification of user identity
If the matching score exceeds a predefined threshold, the user is authenticated successfully.

Payment Processing Module
This module handles transaction operations.
Functions include:
• Accepting payment request
• Verifying authentication result
• Processing payment transaction
• Storing transaction details in database

A transaction record contains:
• Transaction ID
• User ID
• Merchant ID
• Amount
• Date and Time
• Transaction Status

Technologies Used
Programming Language: Python
Libraries: OpenCV, NumPy, SQLite
Dataset: Palm Image Dataset from Kaggle
