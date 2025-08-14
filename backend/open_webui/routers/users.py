import logging
from typing import Optional

from open_webui.models.auths import Auths
from open_webui.models.groups import Groups
from open_webui.models.chats import Chats
from open_webui.models.users import (
    UserModel,
    UserListResponse,
    UserInfoListResponse,
    UserRoleUpdateForm,
    Users,
    UserSettings,
    UserUpdateForm,
)


from open_webui.socket.main import (
    get_active_status_by_user_id,
    get_active_user_ids,
    get_user_active_status,
)
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from open_webui.utils.auth import get_admin_user, get_password_hash, get_verified_user
from open_webui.utils.access_control import get_permissions, has_permission
from open_webui.utils.integrations.stripe.service import StripeService
from open_webui.env import STRIPE_CHECKOUT_PRICE_ID


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter()


############################
# GetActiveUsers
############################


@router.get("/active")
async def get_active_users(
    user=Depends(get_verified_user),
):
    """
    Get a list of active users.
    """
    return {
        "user_ids": get_active_user_ids(),
    }


############################
# GetUsers
############################


PAGE_ITEM_COUNT = 30


@router.get("/", response_model=UserListResponse)
async def get_users(
    query: Optional[str] = None,
    order_by: Optional[str] = None,
    direction: Optional[str] = None,
    page: Optional[int] = 1,
    user=Depends(get_admin_user),
):
    limit = PAGE_ITEM_COUNT

    page = max(1, page)
    skip = (page - 1) * limit

    filter = {}
    if query:
        filter["query"] = query
    if order_by:
        filter["order_by"] = order_by
    if direction:
        filter["direction"] = direction

    return Users.get_users(filter=filter, skip=skip, limit=limit)


@router.get("/all", response_model=UserInfoListResponse)
async def get_all_users(
    user=Depends(get_admin_user),
):
    return Users.get_users()


############################
# User Groups
############################


@router.get("/groups")
async def get_user_groups(user=Depends(get_verified_user)):
    return Groups.get_groups_by_member_id(user.id)


############################
# User Permissions
############################


@router.get("/permissions")
async def get_user_permissisions(request: Request, user=Depends(get_verified_user)):
    user_permissions = get_permissions(
        user.id, request.app.state.config.USER_PERMISSIONS
    )

    return user_permissions


############################
# User Default Permissions
############################
class WorkspacePermissions(BaseModel):
    models: bool = False
    knowledge: bool = False
    prompts: bool = False
    tools: bool = False


class SharingPermissions(BaseModel):
    public_models: bool = True
    public_knowledge: bool = True
    public_prompts: bool = True
    public_tools: bool = True


class ChatPermissions(BaseModel):
    controls: bool = True
    system_prompt: bool = True
    file_upload: bool = True
    file_direct_upload: bool = True
    file_synthetic_enable: bool = True
    delete: bool = True
    edit: bool = True
    share: bool = True
    export: bool = True
    stt: bool = True
    tts: bool = True
    call: bool = True
    multiple_models: bool = True
    temporary: bool = True
    temporary_enforced: bool = False


class FeaturesPermissions(BaseModel):
    direct_tool_servers: bool = False
    web_search: bool = True
    image_generation: bool = True
    code_interpreter: bool = True
    notes: bool = True


class UserPermissions(BaseModel):
    workspace: WorkspacePermissions
    sharing: SharingPermissions
    chat: ChatPermissions
    features: FeaturesPermissions


@router.get("/default/permissions", response_model=UserPermissions)
async def get_default_user_permissions(request: Request, user=Depends(get_admin_user)):
    return {
        "workspace": WorkspacePermissions(
            **request.app.state.config.USER_PERMISSIONS.get("workspace", {})
        ),
        "sharing": SharingPermissions(
            **request.app.state.config.USER_PERMISSIONS.get("sharing", {})
        ),
        "chat": ChatPermissions(
            **request.app.state.config.USER_PERMISSIONS.get("chat", {})
        ),
        "features": FeaturesPermissions(
            **request.app.state.config.USER_PERMISSIONS.get("features", {})
        ),
    }


@router.post("/default/permissions")
async def update_default_user_permissions(
    request: Request, form_data: UserPermissions, user=Depends(get_admin_user)
):
    request.app.state.config.USER_PERMISSIONS = form_data.model_dump()
    return request.app.state.config.USER_PERMISSIONS


############################
# GetUserSettingsBySessionUser
############################


@router.get("/user/settings", response_model=Optional[UserSettings])
async def get_user_settings_by_session_user(user=Depends(get_verified_user)):
    user = Users.get_user_by_id(user.id)
    if user:
        return user.settings
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# UpdateUserSettingsBySessionUser
############################


@router.post("/user/settings/update", response_model=UserSettings)
async def update_user_settings_by_session_user(
    request: Request, form_data: UserSettings, user=Depends(get_verified_user)
):
    updated_user_settings = form_data.model_dump()
    if (
        user.role != "admin"
        and "toolServers" in updated_user_settings.get("ui").keys()
        and not has_permission(
            user.id,
            "features.direct_tool_servers",
            request.app.state.config.USER_PERMISSIONS,
        )
    ):
        # If the user is not an admin and does not have permission to use tool servers, remove the key
        updated_user_settings["ui"].pop("toolServers", None)

    user = Users.update_user_settings_by_id(user.id, updated_user_settings)
    if user:
        return user.settings
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# GetUserInfoBySessionUser
############################


@router.get("/user/info", response_model=Optional[dict])
async def get_user_info_by_session_user(user=Depends(get_verified_user)):
    user = Users.get_user_by_id(user.id)
    if user:
        return user.info
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# UpdateUserInfoBySessionUser
############################


@router.post("/user/info/update", response_model=Optional[dict])
async def update_user_info_by_session_user(
    form_data: dict, user=Depends(get_verified_user)
):
    user = Users.get_user_by_id(user.id)
    if user:
        if user.info is None:
            user.info = {}

        user = Users.update_user_by_id(user.id, {"info": {**user.info, **form_data}})
        if user:
            return user.info
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.USER_NOT_FOUND,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# GetUserById
############################


class UserResponse(BaseModel):
    name: str
    profile_image_url: str
    active: Optional[bool] = None


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str, user=Depends(get_verified_user)):
    # Check if user_id is a shared chat
    # If it is, get the user_id from the chat
    if user_id.startswith("shared-"):
        chat_id = user_id.replace("shared-", "")
        chat = Chats.get_chat_by_id(chat_id)
        if chat:
            user_id = chat.user_id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.USER_NOT_FOUND,
            )

    user = Users.get_user_by_id(user_id)

    if user:
        return UserResponse(
            **{
                "name": user.name,
                "profile_image_url": user.profile_image_url,
                "active": get_active_status_by_user_id(user_id),
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# GetUserActiveStatusById
############################


@router.get("/{user_id}/active", response_model=dict)
async def get_user_active_status_by_id(user_id: str, user=Depends(get_verified_user)):
    return {
        "active": get_user_active_status(user_id),
    }


############################
# UpdateUserById
############################


@router.post("/{user_id}/update", response_model=Optional[UserModel])
async def update_user_by_id(
    user_id: str,
    form_data: UserUpdateForm,
    session_user=Depends(get_admin_user),
):
    log.info(f"User update request: user_id={user_id}, admin={session_user.id}, fields={list(form_data.model_dump(exclude_none=True).keys())}")
    
    # Prevent modification of the primary admin user by other admins
    try:
        first_user = Users.get_first_user()
        if first_user:
            if user_id == first_user.id:
                if session_user.id != user_id:
                    # If the user trying to update is the primary admin, and they are not the primary admin themselves
                    log.warning(f"Unauthorized attempt to modify primary admin: admin={session_user.id}, target={user_id}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=ERROR_MESSAGES.ACTION_PROHIBITED,
                    )

                if form_data.role and form_data.role != "admin":
                    # If the primary admin is trying to change their own role, prevent it
                    log.warning(f"Primary admin attempted to change own role: admin={session_user.id}, new_role={form_data.role}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=ERROR_MESSAGES.ACTION_PROHIBITED,
                    )

    except Exception as e:
        log.error(f"Error checking primary admin status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify primary admin status.",
        )

    user = Users.get_user_by_id(user_id)
    if not user:
        log.error(f"User not found for update: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )

    log.debug(f"Current user data: name={user.name}, email={user.email}, role={user.role}")

    # Collect only provided fields for update
    update_data = {}
    email_to_update = None
    password_to_update = None
    
    # Check email if provided and not empty
    if form_data.email is not None and form_data.email.strip():
        email_lower = form_data.email.lower().strip()
        if email_lower != user.email:
            # Only check for conflicts if email actually changed
            email_user = Users.get_user_by_email(email_lower)
            if email_user:
                log.warning(f"Email conflict during update: user_id={user_id}, email={email_lower}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.EMAIL_TAKEN,
                )
            # Prepare email for update after successful user update
            update_data["email"] = email_lower
            email_to_update = email_lower
            log.info(f"Email change prepared: user_id={user_id}, old_email={user.email}, new_email={email_lower}")
        else:
            log.debug(f"Email unchanged, skipping update: user_id={user_id}, email={email_lower}")
    elif form_data.email is not None and not form_data.email.strip():
        log.warning(f"Empty email provided, ignoring: user_id={user_id}")
    
    # Prepare password for update if provided and not empty
    if form_data.password and form_data.password.strip():
        password_to_update = get_password_hash(form_data.password)
        log.debug(f"Password prepared for update: user_id={user_id}")
    elif form_data.password is not None and not form_data.password.strip():
        log.warning(f"Empty password provided, ignoring: user_id={user_id}")
    
    # Add other fields if provided and not empty
    if form_data.role is not None and form_data.role.strip():
        new_role = form_data.role.strip()
        if new_role != user.role:
            update_data["role"] = new_role
            log.info(f"Role change prepared: user_id={user_id}, old_role={user.role}, new_role={new_role}")
        else:
            log.debug(f"Role unchanged, skipping update: user_id={user_id}, role={new_role}")
    elif form_data.role is not None and not form_data.role.strip():
        log.warning(f"Empty role provided, ignoring: user_id={user_id}")
    
    if form_data.name is not None and form_data.name.strip():
        new_name = form_data.name.strip()
        if new_name != user.name:
            update_data["name"] = new_name
            log.info(f"Name change prepared: user_id={user_id}, old_name={user.name}, new_name={new_name}")
        else:
            log.debug(f"Name unchanged, skipping update: user_id={user_id}, name={new_name}")
    elif form_data.name is not None and not form_data.name.strip():
        log.warning(f"Empty name provided, ignoring: user_id={user_id}")
    
    if form_data.profile_image_url is not None and form_data.profile_image_url.strip():
        new_image_url = form_data.profile_image_url.strip()
        if new_image_url != user.profile_image_url:
            update_data["profile_image_url"] = new_image_url
            log.debug(f"Profile image change prepared: user_id={user_id}, old_url={user.profile_image_url}, new_url={new_image_url}")
        else:
            log.debug(f"Profile image unchanged, skipping update: user_id={user_id}")
    elif form_data.profile_image_url is not None and not form_data.profile_image_url.strip():
        log.warning(f"Empty profile image URL provided, ignoring: user_id={user_id}")

    # Update user data first, then auth data if successful
    if update_data or password_to_update:
        if update_data:
            log.info(f"Updating user fields: user_id={user_id}, fields={list(update_data.keys())}")
            updated_user = Users.update_user_by_id(user_id, update_data)
            if not updated_user:
                log.error(f"Failed to update user in database: user_id={user_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT(),
                )
        else:
            # Only password to update, get current user
            updated_user = user

        # Update auth data only after successful user update
        if email_to_update:
            try:
                Auths.update_email_by_id(user_id, email_to_update)
                log.info(f"Email updated in auth table: user_id={user_id}, new_email={email_to_update}")
            except Exception as e:
                log.error(f"Failed to update email in auth table: user_id={user_id}, error={e}")
                # Consider rolling back user update if auth update fails
                
        if password_to_update:
            try:
                Auths.update_user_password_by_id(user_id, password_to_update)
                log.info(f"Password updated in auth table: user_id={user_id}")
            except Exception as e:
                log.error(f"Failed to update password in auth table: user_id={user_id}, error={e}")
                
        log.info(f"User successfully updated: user_id={user_id}, admin={session_user.id}")
        return updated_user
    else:
        # If no fields to update, return existing user
        log.info(f"No fields to update, returning existing user: user_id={user_id}")
        return user


############################
# DeleteUserById
############################


############################
# Stripe Checkout
############################


class CreateCheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str


@router.post("/stripe/checkout")
async def create_stripe_checkout_session(
    request: CreateCheckoutRequest,
    user=Depends(get_verified_user)
):
    """
    Create a Stripe checkout session for the current user.
    """
    # Get the user details to access stripe_customer_id
    log.info(f"Attempting to create Stripe checkout session for user: {user.id}")
    user_details = Users.get_user_by_id(user.id)
    if not user_details:
        log.error(f"User not found for checkout session: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user_details.stripe_customer_id:
        log.error(f"No Stripe customer ID found for user: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer found for this user"
        )
    
    log.info(f"Creating checkout session for Stripe customer: {user_details.stripe_customer_id} with price_id: {STRIPE_CHECKOUT_PRICE_ID}")
    session = StripeService.create_checkout_session(
        customer_id=user_details.stripe_customer_id,
        price_id=STRIPE_CHECKOUT_PRICE_ID,
        success_url=request.success_url,
        cancel_url=request.cancel_url
    )
    
    if not session:
        log.error(f"Failed to create Stripe checkout session for customer: {user_details.stripe_customer_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )
    
    log.info(f"Stripe checkout session created successfully for user: {user.id}, session_id: {session.id}")
    return {
        "checkout_url": session.url,
        "session_id": session.id
    }


############################
# DeleteUserById
############################


@router.delete("/{user_id}", response_model=bool)
async def delete_user_by_id(user_id: str, user=Depends(get_admin_user)):
    # Prevent deletion of the primary admin user
    try:
        first_user = Users.get_first_user()
        if first_user and user_id == first_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ERROR_MESSAGES.ACTION_PROHIBITED,
            )
    except Exception as e:
        log.error(f"Error checking primary admin status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify primary admin status.",
        )

    if user.id != user_id:
        result = Auths.delete_auth_by_id(user_id)

        if result:
            return True

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DELETE_USER_ERROR,
        )

    # Prevent self-deletion
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ERROR_MESSAGES.ACTION_PROHIBITED,
    )
