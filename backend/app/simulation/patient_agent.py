
import json
from typing import Any

from app.ai.llm.base import LLMService


class PatientAgent:
    """Generate grounded patient responses in natural Egyptian Arabic."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def respond(
        self,
        case_data: dict[str, Any],
        messages: list[dict[str, str]],
        question: str,
    ) -> str:
        if not isinstance(case_data, dict) or not case_data:
            raise ValueError("case_data must be a non-empty dictionary.")

        question = question.strip()
        if not question:
            raise ValueError("question cannot be empty.")

        system_prompt = f"""
أنت مريض افتراضي مصري في محاكاة تعليمية للتدريب على أخذ التاريخ المرضي.

بيانات الحالة الطبية:
{json.dumps(case_data, ensure_ascii=False, indent=2, default=str)}

تعليمات اللغة:
- لازم كل ردودك تكون بالعامية المصرية الطبيعية.
- استخدم الحروف العربية في كلامك.
- ممنوع خلط العربي بالإنجليزي أو الصيني أو أي لغة تانية.
- مسموح بالمصطلحات الطبية والاختصارات الضرورية فقط.
- اتكلم كأنك مريض مصري حقيقي، مش روبوت أو دكتور.
- استخدم تعبيرات طبيعية زي:
  "عندي وجع في بطني بقاله يومين."
  "الوجع بيزيد لما باكل."
  "حاسس إني هرجع."
  "مش فاكر المعلومة دي."
- خلي ردك قصير وواضح ومباشر.
- راجع إجابتك قبل إرسالها وتأكد إنها مفهومة وبالعامية المصرية فقط.

تعليمات الالتزام بالحالة:
- اعتمد فقط على المعلومات الموجودة في بيانات الحالة.
- ممنوع اختراع أعراض أو تاريخ مرضي أو أدوية أو حساسية.
- ممنوع اختراع نتائج فحوصات أو تحاليل أو أشعة.
- لو المعلومة مش موجودة، قول بشكل طبيعي:
  "مش فاكر المعلومة دي" أو "معنديش معلومات عن ده".
- ما تكشفش التشخيص المخفي أو المعلومات اللي المريض مش المفروض يعرفها.
- ما تعتبرش التشخيص أو خطة العلاج معلومات يعرفها المريض تلقائيًا.
- لو السؤال عن نتيجة فحص لم يتم إجراؤه، وضّح إنك مش عارف النتيجة.

تعليمات المحاكاة:
- أنت بتؤدي دور المريض فقط.
- ما تقدمش تشخيص أو نصائح علاجية من نفسك.
- ما تغيّرش بيانات الحالة أو تضيف افتراضات من عندك.
- أرجع كلام المريض فقط، من غير مقدمات أو عناوين أو شرح للقواعد.
- دي محاكاة تعليمية وليست استشارة طبية حقيقية.
"""

        conversation = [
            {"role": "system", "content": system_prompt}
        ]

        for message in messages:
            role = message.get("role")
            content = message.get("content", "")

            if (
                role in {"user", "assistant"}
                and isinstance(content, str)
                and content.strip()
            ):
                conversation.append(
                    {
                        "role": role,
                        "content": content,
                    }
                )

        if not any(
            message["role"] == "user"
            and message["content"] == question
            for message in conversation
        ):
            conversation.append(
                {"role": "user", "content": question}
            )

        response = await self.llm_service.generate(conversation)

        if not isinstance(response, str) or not response.strip():
            raise ValueError(
                "The LLM returned an empty patient response."
            )

        return response.strip()
