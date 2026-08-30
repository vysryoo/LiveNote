import type { QnA, Resource } from "../services/ports";

// 공통 스트리밍 카드 타입
// - QnA / Resource 모두 이 모델을 통해 스트리밍됨
// - QnA의 세부 타입(concept, application, ...)은 QnA.type에 포함되어 있고
//   별도 qnaType 필드는 두지 않는다.
// - Resource의 세부 타입(paper, wiki, video, blog)은
//   data(Resource.type) 뿐 아니라, 스트리밍 중 스타일링을 위해
//   resourceType 필드로 한 번 더 들고 있을 수 있다.
export interface StreamingCard {
  cardId: string;
  type: "qna" | "resource";
  cardIndex: number;
  content: string;
  isComplete: boolean;
  data?: QnA | Resource;
  error?: string;
  resourceType?: "paper" | "wiki" | "video" | "blog";
  title?: string;
}
