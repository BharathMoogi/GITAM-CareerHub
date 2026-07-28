import { aiApi } from '../api/ai';

export const useAI = () => {
  return {
    sendMessage: (prompt: string, context?: any) => aiApi.sendMessage(prompt, context),
    getRecommendation: () => aiApi.getRecommendation(),
  };
};
