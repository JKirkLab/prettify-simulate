# prettify-simulate

A small module designed to make the output of opentrons simulate more readable. To change which protocol is simulated, edit the file path present in line 13. This can be eventually changed to a GUI for easier access. 

The script parses the output of the simulate module opentrons provides natively. It attempts to extract known output patterns, such as Aspirating, Dispensing, Picking up/ Dropping tips etc. Additionally, the program attempts to group actions based on a source to destination criteria. 

The output of the module displays the simplified protocol using Rich. 