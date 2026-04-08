import 'package:flutter/foundation.dart';

class ProfanityFilter {
  // A curated list of offensive terms in English, Hindi, and Hinglish.
  // In a production app, this would be much more extensive or use an API.
  static final List<String> _badWords = [
    // English (subset for demonstration)
    'badword', 'offensive', 'spam', 'scam', 'fake', 'abuse',
    'fuck', 'shit', 'asshole', 'bitch', 'dick', 'pussy',
    
    // Hindi/Hinglish (common terms used in misinformation/abuse)
    'chutiya', 'gaand', 'randi', 'harami', 'kamina', 'bhenchod', 'madarchod',
    'saala', 'kutte', 'suar', 'haramkhor', 'bakwas', 'jhooth', 'chor',
    
    // New Dataset terms from PDFs
    'motherfucker', 'maaderchod', 'chinaal', 'rakhita', 'bollocks', 
    'bastard', 'bloody', 'cunt', 'slut', 'whore', 'scoundrel'
  ];

  /// Checks if the input contains any bad words.
  /// Returns the first bad word found, or null if clean.
  static String? detectBadWord(String input) {
    if (input.isEmpty) return null;
    
    final lowerInput = input.toLowerCase();
    
    for (final badWord in _badWords) {
      if (lowerInput.contains(badWord.toLowerCase())) {
        return badWord;
      }
    }
    return null;
  }

  /// Removes all known bad words from the input string.
  static String cleanText(String input) {
    String output = input;
    for (final word in _badWords) {
      // Aggressive substring deletion (no word boundaries) 
      // ensures words are wiped as they are typed.
      final regExp = RegExp(RegExp.escape(word), caseSensitive: false);
      output = output.replaceAll(regExp, '');
    }
    // Clean up excessive spaces
    return output.replaceAll(RegExp(r'\s{2,}'), ' ').trim();
  }
}
