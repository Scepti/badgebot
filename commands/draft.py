from header import *
async def draft(message, args):
  user = getmention(message)
  if user == None:
    userid = discorduser_to_id(message.author)
  else:
    userid = discorduser_to_id(user)
    args = args.split(maxsplit=1)[1]
  cursor.execute(draft_select_str, (userid,))
  result = cursor.fetchone()
  if result == None:
    await client.send_message(message.channel, "You are not in the draft league")
    return
  sheet = SHEET_IDS[result[0]]
  mon_col = TEAM_COLS[result[1]]
  point_col = POINT_COLS[result[1]]
  # Get all the cells of pokemon tiers
  tiers = service.spreadsheets().values().get(spreadsheetId=sheet, range='Tiers', majorDimension='COLUMNS').execute()
  values = tiers.get('values', [])
  # Get all the currently drafted Pokemon
  drafted = service.spreadsheets().values().get(spreadsheetId=sheet,range='Rosters', majorDimension='COLUMNS').execute()
  mons = drafted.get('values', [])
  for col in mons:
    if args in col:
      await client.send_message(message.channel, 'That pokemon has already been drafted')
      return
  found = False
  for i, tier in enumerate(values):
    if args in tier:
      tierLevel = values[i][0]
      cost = values[i+1][0][1:-1]
      msg = tierLevel + ' Cost: ' + cost
      found = True

      cellRow = tier.index(args)

      strike = [{'updateCells':{
        'rows': [{
          'values':[{
            'userEnteredFormat': {
              'textFormat':{
                'strikethrough': True
                }
              }
            }]
          }],
        'fields': 'userEnteredFormat.textFormat.strikethrough',
        'range': {
          'sheetId': 161954080,
          'startRowIndex': cellRow,
          'endRowIndex': cellRow+1,
          'startColumnIndex': i,
          'endColumnIndex': i+1
          }

        }}]
      body = {'requests':strike}
      response = service.spreadsheets().batchUpdate(spreadsheetId=sheet, body=body).execute()
      # Update Roster page
      # First, create a list of possible rows
      if 'M' in tierLevel: #If mon is mega
        rows = [12]
      else:
        if '1' in tierLevel:
          rows = [6]
        if '2' in tierLevel:
          rows = [7]
        if '3' in tierLevel:
          rows = [8,9]
        if '4' in tierLevel:
          rows = [10]
        if '5' in tierLevel:
          rows = [11]
        rows.extend([13, 14, 15, 16])
      # Now, find the first row in rows that isn't filled in
      for row in rows:
        roster =service.spreadsheets().values().get(spreadsheetId=sheet,range='Rosters!'+mon_col+str(row), majorDimension='COLUMNS').execute()
        roster = roster.get('values', [])
        if len(roster) == 0: # If the current cell is empty
          service.spreadsheets().values().update(spreadsheetId=sheet, range='Rosters!'+mon_col+str(row)+':'+point_col+str(row),
              body={'majorDimension':'ROWS','values':[[args, None, cost]], 'range':'Rosters!'+mon_col+str(row)+':'+point_col+str(row)}, valueInputOption='USER_ENTERED').execute()
          # Next, add it to the draft column
          draftlist = service.spreadsheets().values().get(spreadsheetId=sheet,range='Draft!B3:B', majorDimension='COLUMNS').execute()
          draftcount = len(draftlist.get('values', [])[0]) + 3
          service.spreadsheets().values().update(spreadsheetId=sheet, range='Draft!B'+str(draftcount), body={'majorDimension':'ROWS', 'values':[[args]], 'range':'Draft!B'+str(draftcount)}, valueInputOption='USER_ENTERED').execute()
          await client.send_message(message.channel, 'Done')
          return
  msg = 'This is not a pokemon you can draft'
  await client.send_message(message.channel, msg)
