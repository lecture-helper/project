import sys
import nltk 
#download 'all' nltk corpora on server 

def processInputList(input_list): 
	noun_tag_list = []
	for question in input_list: 
		tokens = nltk.word_tokenize(question)
		tagged = nltk.pos_tag(tokens)
		for word in tagged: 
			if word[1] =='NN' or word[1] == 'NNP' or word[1]== 'NNPS' or word[1]== 'PRP': #tags are just nouns for the time being
				noun_tag_list.append(word[0])


	return noun_tag_list

def find_frequencies_for_each_question(input_list, noun_tag_list):
	question_score_dict = {}
	for question in input_list: 
		score = 0
		reformatted_question = question.replace("!", "").replace(".", "").replace("?", "")
		reformatted_question_list = reformatted_question.split(" ")
		for noun in noun_tag_list: 
			if noun in reformatted_question_list:
				score += 1
		question_score_dict[question] = score
	return question_score_dict


def relevantQuestions(input_list, num_results): 
	noun_tag_list = processInputList(input_list)
	question_score_dict = find_frequencies_for_each_question(input_list, noun_tag_list)
	newQuestionList = sorted(question_score_dict, key=question_score_dict.__getitem__)

	if len(newQuestionList) < num_results:
		num_results = len(newQuestionList)
	return newQuestionList[0:num_results]

def main():
	input_list = ["what is a program?", "what is a compiler?", "what is a computer?", "how do compilers work?", "how do programs work?"]
	print relevantQuestions(input_list, 10)

if __name__ == '__main__':
	main()

	
			
