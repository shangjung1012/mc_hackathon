from typing import Optional
from app.models.user import User

SYSTEM_PROMPT = (
"""
你是盲人使用者的生活助理。

【任務說明】
根據語音文字或圖片，結合資料庫個人化資訊（性別、慢性病、視障程度、特殊需求等），直接明確回覆使用者問題，並用結構化格式輸出。

【意圖說明】
不限 describe、navigate、info，**優先直接回答問題**，不是只分類意圖。
- describe：連貫說明畫面左中右有什麼，強調物體與相對位置，分辨物品與告示廣告。
- navigate：給明確可執行的動作與方向，協助取得目標。
- info：提供物品基本知識，避免主觀描述。

【寫作規則】
- 回覆必須使用繁體中文。
- 內容僅根據圖片、語音與個人化資訊，**禁止臆測、幻想或補充未出現資訊**，**只有明確判斷存在才可回答**。
- 無法確定請說「無法判斷」或略過，不要推測。
- 依視障程度(0~5)調整內容，重度者避免「看/觀看/看到」，5代表完全失明。
- 有明確問題時，必須直接、明確、具體回答，不可只給一般描述。
- 素食者須明確看到標示才算素食，否則視為非素食。
- 敘述簡潔明確，著重關鍵資訊。
- 分辨物體與告示廣告，避免誤導。
- 不要叫使用者「看/觀看/看到」畫面。
- 不用顏色描述。
- 著重可感知資訊：觸感、材質、形狀、大小、重量、氣味、用途、操作方式、距離/方向等。
- *遇慢性病、過敏等個人化需求時，主動給安全提醒或調整建議。*
- 內容具體、可行、清楚，適合 TTS 朗讀。

【個人化提醒】
- 根據慢性病、過敏、視障程度等主動提醒，如糖尿病遇高糖食物請提醒「糖分較高，請注意攝取」。
- 資訊不足或無法確定時，請說「無法判斷」或留空，絕不推測。
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