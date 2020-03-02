def parse_string(string, sep=None):
	word_list = [i.lower() for i in string.split(sep)]
	cleaned_list = []
	for word in word_list:
		cleaned_word = ''
		for symb in word:
			if symb.isalpha() or symb.isdigit() or symb == ' ':
				cleaned_word += symb
			else:
				cleaned_word += ' '
		cleaned_word = cleaned_word.strip()
		if cleaned_word and cleaned_word not in cleaned_list: cleaned_list.append(cleaned_word)
	return cleaned_list

