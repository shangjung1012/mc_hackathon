from typing import Optional
from app.models.user import User

SYSTEM_PROMPT = (
"""
你是盲人使用者的視覺助理。

任務：依「語音文字」與「圖片」判斷唯一意圖，並用已定義的結構化輸出回覆。

意圖僅三種：
- **describe**：以一段連貫語句概述畫面的左中右分別有什麼。描述應著重於物體與其相對位置，確實判斷是一個物品還是是告示廣告，例如：「前方有貨架，左邊是餅乾，右邊是零食。」
- **navigate**：提供一段清楚、可執行的動作與方向，協助取得圖中目標。例如：「請向前走三步，然後將手伸向右前方。」
- **info**：提供所問物品的基本知識，避免主觀感覺描述。例如：「這款洗髮精為按壓瓶，容量500毫升。」或「這是一盒12顆裝的雞蛋。」

寫作規則（必守）：
- **內容必須基於圖片與語音中的實際觀察**，避免任何臆測或幻覺。
- **敘述必須簡潔明確**，著重於關鍵資訊。
- **不要叫使用者「看/觀看/看到」** 畫面。
- **不要使用任何「顏色」描述**。
- **著重可感知資訊**：觸感、材質、形狀、大小、重量、氣味、用途、操作方式、距離/方向等。
- 內容需具體、可行、清楚，能直接用 TTS 朗讀。

**若資訊不足，請給出安全、合理的預設或留空**。
"""
)

def get_system_prompt_with_user(user: Optional[User]) -> str:
    """
    根據使用者資料生成個性化的 system prompt
    """
    if not user:
        return SYSTEM_PROMPT
    
    # 構建使用者資訊部分
    user_info_parts = []
    
    # 基本資訊
    user_info_parts.append(f"使用者名稱：{user.username}")
    
    # 性別和年齡
    if user.gender:
        gender_text = {"male": "男性", "female": "女性", "other": "其他"}.get(user.gender.value, user.gender.value)
        user_info_parts.append(f"性別：{gender_text}")
    
    if user.age:
        user_info_parts.append(f"年齡：{user.age}歲")
    
    # 視力狀況
    if user.vision_level:
        vision_descriptions = {
            0: "接近正常視力",
            1: "輕度視障",
            2: "中度視障", 
            3: "重度視障",
            4: "極重度視障",
            5: "完全失明"
        }
        vision_text = vision_descriptions.get(user.vision_level.value, f"視力等級 {user.vision_level.value}")
        user_info_parts.append(f"視力狀況：{vision_text}")
    
    # 慢性病
    if user.chronic_diseases:
        diseases_text = "、".join(user.chronic_diseases)
        user_info_parts.append(f"慢性病：{diseases_text}")
    
    # 其他資訊
    if user.others:
        user_info_parts.append(f"其他資訊：{user.others}")
    
    # 組合使用者資訊
    user_info = "\n".join(user_info_parts)
    
    # 根據視力狀況調整提示
    vision_guidance = ""
    if user.vision_level:
        if user.vision_level.value >= 4:  # 重度視障或完全失明
            vision_guidance = "\n\n**特別注意**：此使用者為重度視障或完全失明，請特別注重觸覺、聽覺、嗅覺等非視覺感官的描述，提供更詳細的空間定位和物體識別資訊。"
        elif user.vision_level.value >= 2:  # 中度視障
            vision_guidance = "\n\n**特別注意**：此使用者為中度視障，請提供清晰的空間描述和物體識別資訊，避免依賴細微的視覺細節。"
        elif user.vision_level.value >= 1:  # 輕度視障
            vision_guidance = "\n\n**特別注意**：此使用者為輕度視障，請提供清晰的描述，但可以包含一些基本的視覺資訊。"
    
    # 根據年齡調整提示
    age_guidance = ""
    if user.age:
        if user.age >= 65:
            age_guidance = "\n\n**特別注意**：此使用者為長者，請使用更簡單、清晰的語言，避免複雜的術語，並考慮長者可能的身體限制。"
        elif user.age <= 18:
            age_guidance = "\n\n**特別注意**：此使用者為青少年或兒童，請使用適合其年齡的語言，並提供安全相關的提醒。"
    
    # 根據慢性病調整提示
    health_guidance = ""
    if user.chronic_diseases:
        health_guidance = "\n\n**特別注意**：此使用者有慢性病，在提供建議時請考慮其健康狀況，避免可能影響健康的建議。"
    
    # 組合完整的 system prompt
    personalized_prompt = f"""{SYSTEM_PROMPT}

**當前使用者資訊**：
{user_info}{vision_guidance}{age_guidance}{health_guidance}

請根據以上使用者資訊，提供更個性化和適合的協助。"""
    
    return personalized_prompt