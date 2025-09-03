    def calculate_toxicity_score(self, text, label, sentiment_data):
        base_score = 0.0

        # Labels précis pour ton dataset
        if label.upper() == 'B':  # Bullying
            base_score += 0.7
        elif label.upper() == 'NB':  # Not Bullying
            base_score += 0.1
        else:
            # Cas imprévu, on reste faible
            base_score += 0.1
        
        # Score VADER compound (valeurs entre -1 et 1)
        vader_compound = sentiment_data.get('vader_compound', 0)
        if vader_compound < -0.5:
            base_score += 0.2
        elif vader_compound < -0.2:
            base_score += 0.1

        # Bonus si le texte est long (>10 mots)
        if text and len(text.split()) > 10:
            base_score += 0.1

        return min(1.0, base_score)