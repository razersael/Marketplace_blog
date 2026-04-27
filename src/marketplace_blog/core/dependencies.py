from fastapi import HTTPException, Request, status


def get_current_user_id(request: Request) -> int:
    """
    Возвращает ID текущего пользователя из middleware.
    Используется для проверки прав при создании/редактировании/удалении.
    """
    user_id = getattr(request.state, "user_id", None)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    return user_id
