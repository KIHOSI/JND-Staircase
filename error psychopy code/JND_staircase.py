"""measure your JND in orientation using a staircase method"""
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
import numpy, random
import csv

try:  # try to get a previous parameters file
    expInfo = fromFile('lastParams.pickle')
except:  # if not there then use a default set
    expInfo = {'observer':'jwp', 'refOrientation':0}
expInfo['dateStr'] = data.getDateStr()  # add the current time
# present a dialogue to change params
dlg = gui.DlgFromDict(expInfo, title='simple JND Exp', fixed=['dateStr'])
if dlg.OK:
    toFile('lastParams.pickle', expInfo)  # save params to file for next time
else:
    core.quit()  # the user hit cancel so exit

# # make a text file to save data
fileName = expInfo['observer'] + expInfo['dateStr']
# dataFile = open(fileName+'.csv', 'w')  # a simple text file with 'comma-separated-values'
# dataFile.write('targetSide,oriIncrement,correct\n')

# win = visual.Window([800,600], color='grey', units='deg')

# Log file
dataFile = open('blade_JND_data.csv', 'w', newline='')
writer = csv.writer(dataFile)
writer.writerow(['targetSide', 'bladeAngle', 'response', 'correct'])

# create the staircase handler
staircase = data.StairHandler(startVal = 45,
                              stepType = 'lin', 
                              stepSizes=[10,5,2], 
                              minVal=0,
                              maxVal=90,
                              nUp=1, 
                              nDown=3,  # will home in on the 80% threshold
                              nReversals=6,
                              nTrials=50,
                              method='staircase')


# create window
win = visual.Window([800,600],allowGUI=True,
                    monitor='testMonitor', units='deg')
# Create stimuli
fixation = visual.TextStim(win, text='+', height=1)
blade_left = visual.Rect(win, width=1, height=5, fillColor='white', pos=(-5, 0))
blade_right = visual.Rect(win, width=1, height=5, fillColor='white', pos=(5, 0))

# foil = visual.GratingStim(win, sf=1, size=4, mask='gauss',
#                           ori=expInfo['refOrientation'])
# target = visual.GratingStim(win, sf=1, size=4, mask='gauss',
#                             ori=expInfo['refOrientation'])
# fixation = visual.GratingStim(win, color=-1, colorSpace='rgb',
#                               tex=None, mask='circle', size=0.2)
# and some handy clocks to keep track of time
# globalClock = core.Clock()
# trialClock = core.Clock()s

# display instructions and wait
message1 = visual.TextStim(win, pos=[0,+3],text='Hit a key when ready.')
# message2 = visual.TextStim(win, pos=[0,-3],
#     text="Then press left or right to identify the %.1f deg probe." %expInfo['refOrientation'])
message2 = visual.TextStim(win, pos=[0,-3],
    text="Press 'left' if the first stimulus felt stronger, 'right' if the second did.")
message3 = visual.TextStim(win, pos=[0,-5],
    text="Press 'space' to repeat the trial if unsure.")
message1.draw()
message2.draw()
message3.draw()
fixation.draw()
win.flip()#to show our newly drawn 'stimuli'
#pause until there's a keypress
event.waitKeys()

# Experiment loop
for bladeAngle in staircase:
    print(f"Trial #{staircase.thisTrialN}, bladeAngle = {bladeAngle}")
    # randomly pick which side shows the angle (left or right)
    targetSide = random.choice(['left', 'right'])

    if targetSide == 'left':
        angle_left = 90
        angle_right = 90 - bladeAngle
    else:
        angle_left = 90  - bladeAngle
        angle_right = 90

    # apply rotation to blades; make angle = 0 表示 水平（平躺）, angle = 90 表示 垂直

    blade_left.ori = 90 - angle_left
    blade_right.ori = 90 - angle_right

    # # show fixation
    # fixation.draw()
    # win.flip()
    # core.wait(0.5)

    # # show stimuli
    # blade_left.draw()
    # blade_right.draw()
    # win.flip()

    # allow repeat trial until users click 'left' or 'right'
    repeatTrial = True
    while repeatTrial:
        # show fixation
        fixation.draw()
        win.flip()
        core.wait(0.5)

        # show stimuli
        blade_left.draw()
        blade_right.draw()
        win.flip()

        # get response
        thisResp = None
        repeatNow = False
        while thisResp is None:
            allKeys = event.waitKeys(keyList=['left', 'right', 'space', 'q', 'escape'])
            print("Key pressed:", allKeys)  # <-- debug line
            for thisKey in allKeys:
                if thisKey == 'space':
                    print("Repeating trial...")
                    repeatNow = True
                    break
                elif thisKey=='left':
                    if targetSide== 'left': thisResp = 1  # correct
                    else: thisResp = -1              # incorrect
                    repeatTrial = False
                elif thisKey=='right':
                    if targetSide== 'right': thisResp = 1  # correct
                    else: thisResp = -1              # incorrect
                    repeatTrial = False
                elif thisKey in ['q', 'escape']:
                    core.quit()  # abort experiment
            event.clearEvents()  # clear other (eg mouse) events - they clog the buffer

            if repeatNow is True:
                break



    # wait for response
    # keys = event.waitKeys(keyList=['left', 'right'])
    # response = keys[0]

    # # determine correctness
    # correct = ((response == 'left' and targetSide == 'left') or
    #            (response == 'right' and targetSide == 'right'))

    # update staircase
    correct = (thisResp == 1)
    print(correct, type(correct))  # 加這行會看到是什麼型別
    staircase.addData(correct)

    # log data
    writer.writerow([targetSide, bladeAngle, thisKey, thisResp])

    # inter-trial interval
    fixation.draw()
    win.flip()
    core.wait(1)

    # if staircase.finished:
    #     break

    if len(staircase.reversalIntensities) >= 6:
        break


# staircase has ended
dataFile.close()
staircase.saveAsPickle(fileName)  # special python binary file to save all the info

# give some output to user in the command line in the output window
print('reversals:')
print(staircase.reversalIntensities)
approxThreshold = numpy.average(staircase.reversalIntensities[-6:])
print('mean of final 6 reversals = %.3f' % (approxThreshold))

# give some on-screen feedback
feedback1 = visual.TextStim(
        win, pos=[0,+3],
        text='mean of final 6 reversals = %.3f' % (approxThreshold))

feedback1.draw()
fixation.draw()
win.flip()
event.waitKeys()  # wait for participant to respond

win.close()
core.quit()