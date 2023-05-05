from accessor import ChatAccessor

accessor = ChatAccessor('sqlite:///db/chat.db')

for i in accessor.get_all_message_by_id_to_id(8, 1):
    print(i.text)
