i want to add email functionality for:
messages sent confirmation
applications sent confirmation
allow message replies in the portal message that automatically sends email
integration of an omegabetaeta@umich.edu email that sends the emails from messages and recieves the messages


i also want to overhaul the default password creation, i want everyone to get a password of 8 randomly generated numbers that is stored in sql unhashed, and then sent to all of the emails in the brothers db (uniqname@umich.edu) and a bit in each brother indicating email sent, and a bit indicating password changed for first time. There should be a button in the directory that sends the password of each brother and a link to the site to each brother that hasnt been sent an email, and president or admin should be able to do this. there should also be a button on each individual brother that sends a newly generated default password, disregarding password changed or email sent, able to be used by admin or president for password resets or another reminder. 

The default password should only work if the password changed bit is false, and once the brother logs in with the default password, they should be forced to change it. Clicking the button on an individual brother would set the bit indicating password changed to false, and then send the default password to the brother, and force change again. 

Admin and pres should be able to see if a brother password has been unchanged or if email was sent to brother when clicking on them in directory, and also see a list of all brothers that have not had an email sent to them, and be able to send the default password to all of those brothers with one click.

Newly moved recruits should also get the default password email, and have the same functionality as above.

You have final discretion over how this should work and best practices, these are just general guidelines for the functionality I want to add. I want you to design the best system for this, and implement it in the best way possible.

update help docs to reflect changes