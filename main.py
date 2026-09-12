from datetime import date, timedelta
from decimal import Decimal

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User, Expense

from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    AdminUserResponse,
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    UserUpdateRequest,
    PasswordUpdateRequest,
)

from auth import (
    get_current_user,
    require_admin,
    require_user,
    hash_password,
    verify_password,
    create_access_token,
)

from ai_service import analyze_expenses


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Cloud Expense Management System",
    description="Cloud-based expense management system with AI analysis",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://expense-manager-gilt-ten.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Cloud Expense Management System API",
        "status": "running"
    }


# ============================================================
# AUTHENTICATION
# ============================================================

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == request.email
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(
        name=request.name,
        email=request.email,
        password=hash_password(request.password),
        salary=request.salary,
        role="user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ============================================================
# LOGIN
# ============================================================

@app.post(
    "/auth/login",
    response_model=TokenResponse
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == request.email
    ).first()

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(
        request.password,
        user.password
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(
        user_id=user.user_id,
        role=user.role
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ============================================================
# CURRENT USER
# ============================================================

@app.get(
    "/users/me",
    response_model=UserResponse
)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):

    return current_user


# ============================================================
# UPDATE CURRENT USER PROFILE
# ============================================================

@app.put(
    "/users/me",
    response_model=UserResponse
)
def update_my_profile(
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------------
    # Get the user again using THIS endpoint's DB session.
    # --------------------------------------------------------

    user = db.query(User).filter(
        User.user_id == current_user.user_id
    ).first()

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # --------------------------------------------------------
    # Check email uniqueness
    # --------------------------------------------------------

    existing_user = db.query(User).filter(
        User.email == request.email,
        User.user_id != user.user_id
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # --------------------------------------------------------
    # Update editable profile fields
    # --------------------------------------------------------

    user.name = request.name
    user.email = request.email
    user.salary = request.salary

    # --------------------------------------------------------
    # IMPORTANT:
    # Role is intentionally NOT updated.
    # --------------------------------------------------------

    db.commit()

    # Refresh the object belonging to THIS session.
    db.refresh(user)

    return user


# ============================================================
# CHANGE CURRENT USER PASSWORD
# ============================================================

@app.put(
    "/users/me/password"
)
def update_my_password(
    request: PasswordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------------
    # Get the latest user record in THIS DB session
    # --------------------------------------------------------

    user = db.query(User).filter(
        User.user_id == current_user.user_id
    ).first()

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # --------------------------------------------------------
    # Verify current password
    # --------------------------------------------------------

    if not verify_password(
        request.current_password,
        user.password
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # --------------------------------------------------------
    # Generate a new bcrypt hash
    # --------------------------------------------------------

    new_hashed_password = hash_password(
        request.new_password
    )

    # --------------------------------------------------------
    # Update password
    # --------------------------------------------------------

    user.password = new_hashed_password

    # Force SQLAlchemy to send the update
    db.flush()

    # Permanently save the change
    db.commit()

    # Reload from database
    db.refresh(user)

    # --------------------------------------------------------
    # Verify that the new password was actually persisted
    # --------------------------------------------------------

    if not verify_password(
        request.new_password,
        user.password
    ):

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password update failed"
        )

    return {
        "message": "Password updated successfully"
    }


# ============================================================
# ADMIN
# ============================================================

@app.get(
    "/admin/users",
    response_model=list[AdminUserResponse]
)
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):

    users = db.query(User).order_by(
        User.user_id
    ).all()

    return users


# ============================================================
# HELPER FUNCTIONS FOR AI / FINANCIAL CALCULATIONS
# ============================================================

def get_month_boundaries(today: date):

    next_month = (
        today.replace(day=28)
        + timedelta(days=4)
    ).replace(day=1)

    return next_month


def calculate_days_remaining(today: date):

    next_month = get_month_boundaries(today)

    return (next_month - today).days


# ============================================================
# GET ALL EXPENSES
# ============================================================

@app.get(
    "/expenses",
    response_model=list[ExpenseResponse]
)
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):

    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.user_id
    ).order_by(
        Expense.expense_date.desc(),
        Expense.expense_id.desc()
    ).all()

    return expenses


# ============================================================
# GET SINGLE EXPENSE
# ============================================================

@app.get(
    "/expenses/{expense_id}",
    response_model=ExpenseResponse
)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):

    expense = db.query(Expense).filter(
        Expense.expense_id == expense_id,
        Expense.user_id == current_user.user_id
    ).first()

    if expense is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return expense


# ============================================================
# CREATE EXPENSE + AI ANALYSIS
# ============================================================

@app.post(
    "/expenses",
    status_code=status.HTTP_201_CREATED
)
def create_expense(
    request: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):

    # --------------------------------------------------------
    # Create expense
    # --------------------------------------------------------

    new_expense = Expense(
        user_id=current_user.user_id,
        title=request.title,
        amount=request.amount,
        category=request.category,
        description=request.description,
        expense_date=request.expense_date
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)


    # --------------------------------------------------------
    # Today's date
    # --------------------------------------------------------

    today = date.today()


    # --------------------------------------------------------
    # Get ALL expenses for this user
    # --------------------------------------------------------

    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.user_id
    ).order_by(
        Expense.expense_date.desc()
    ).all()


    # ========================================================
    # CURRENT MONTH EXPENSES
    # ========================================================

    current_month_expenses = [
        expense
        for expense in expenses
        if (
            expense.expense_date.year == today.year
            and expense.expense_date.month == today.month
            and expense.expense_date <= today
        )
    ]


    # ========================================================
    # FUTURE EXPENSES
    # ========================================================

    future_expenses = [
        expense
        for expense in expenses
        if expense.expense_date > today
    ]


    # --------------------------------------------------------
    # Financial calculations
    # --------------------------------------------------------

    total_spent = sum(
        (
            expense.amount
            for expense in current_month_expenses
        ),
        Decimal("0")
    )

    remaining_balance = (
        current_user.salary - total_spent
    )

    days_remaining = calculate_days_remaining(today)


    if days_remaining > 0:

        daily_spending_limit = (
            remaining_balance / Decimal(days_remaining)
        )

        if daily_spending_limit < 0:
            daily_spending_limit = Decimal("0")

    else:

        daily_spending_limit = Decimal("0")


    # --------------------------------------------------------
    # Future expense calculations
    # --------------------------------------------------------

    future_expenses_total = sum(
        (
            expense.amount
            for expense in future_expenses
        ),
        Decimal("0")
    )

    projected_balance = (
        remaining_balance - future_expenses_total
    )


    # --------------------------------------------------------
    # Previous expenses
    # --------------------------------------------------------

    previous_expenses = [
        expense
        for expense in expenses
        if (
            expense.expense_id != new_expense.expense_id
            and expense.expense_date < new_expense.expense_date
        )
    ]


    # --------------------------------------------------------
    # Related expenses
    # --------------------------------------------------------

    related_expenses = [
        expense
        for expense in previous_expenses
        if expense.category.lower()
        == new_expense.category.lower()
    ]


    related_expenses_total = sum(
        (
            expense.amount
            for expense in related_expenses
        ),
        Decimal("0")
    )


    # --------------------------------------------------------
    # New expense impact
    # --------------------------------------------------------

    if remaining_balance > 0:

        percentage_of_remaining_balance = (
            new_expense.amount
            / remaining_balance
        ) * Decimal("100")

    else:

        percentage_of_remaining_balance = Decimal("100")


    if daily_spending_limit > 0:

        equivalent_days_of_daily_budget = (
            new_expense.amount
            / daily_spending_limit
        )

    else:

        equivalent_days_of_daily_budget = Decimal("0")


    # ========================================================
    # AI INPUT
    # ========================================================

    financial_data = {

        "user": {
            "name": current_user.name
        },

        "salary": str(
            current_user.salary
        ),

        "today": str(today),

        "current_month": {

            "days_remaining": days_remaining,

            "total_spent": str(
                total_spent
            ),

            "remaining_balance": str(
                remaining_balance
            ),

            "daily_spending_limit": str(
                daily_spending_limit
            )
        },

        "new_expense": {

            "title": new_expense.title,

            "amount": str(
                new_expense.amount
            ),

            "category": new_expense.category,

            "description": new_expense.description,

            "expense_date": str(
                new_expense.expense_date
            ),

            "is_future": (
                new_expense.expense_date > today
            ),

            "percentage_of_remaining_balance": str(
                percentage_of_remaining_balance.quantize(
                    Decimal("0.01")
                )
            ),

            "equivalent_days_of_daily_budget": str(
                equivalent_days_of_daily_budget.quantize(
                    Decimal("0.01")
                )
            )
        },

        # ----------------------------------------------------
        # Previous expenses
        # ----------------------------------------------------

        "previous_expenses": [

            {
                "title": expense.title,

                "amount": str(
                    expense.amount
                ),

                "category": expense.category,

                "description": expense.description,

                "expense_date": str(
                    expense.expense_date
                )

            }

            for expense in previous_expenses
        ],


        # ----------------------------------------------------
        # Related expenses
        # ----------------------------------------------------

        "related_expenses": {

            "category": new_expense.category,

            "count": len(
                related_expenses
            ),

            "total": str(
                related_expenses_total
            ),

            "expenses": [

                {
                    "title": expense.title,

                    "amount": str(
                        expense.amount
                    ),

                    "expense_date": str(
                        expense.expense_date
                    )

                }

                for expense in related_expenses
            ]
        },


        # ====================================================
        # FUTURE / PLANNED EXPENSES
        # ====================================================

        "future_expenses": {

            "count": len(
                future_expenses
            ),

            "total": str(
                future_expenses_total
            ),

            "projected_balance": str(
                projected_balance
            ),

            "expenses": [

                {
                    "title": expense.title,

                    "amount": str(
                        expense.amount
                    ),

                    "category": expense.category,

                    "description": expense.description,

                    "expense_date": str(
                        expense.expense_date
                    )

                }

                for expense in future_expenses
            ]
        }
    }


    # ========================================================
    # CALL AI
    # ========================================================

    ai_analysis = None

    try:

        ai_analysis = analyze_expenses(
            financial_data
        )

    except Exception as e:

        print(
            "AI analysis failed:",
            str(e)
        )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "expense": new_expense,

        "ai_analysis": ai_analysis
    }


# ============================================================
# UPDATE EXPENSE
# ============================================================

@app.put(
    "/expenses/{expense_id}",
    response_model=ExpenseResponse
)
def update_expense(
    expense_id: int,
    request: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):

    expense = db.query(Expense).filter(
        Expense.expense_id == expense_id,
        Expense.user_id == current_user.user_id
    ).first()

    if expense is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )


    expense.title = request.title
    expense.amount = request.amount
    expense.category = request.category
    expense.description = request.description
    expense.expense_date = request.expense_date

    db.commit()
    db.refresh(expense)

    return expense


# ============================================================
# DELETE EXPENSE
# ============================================================

@app.delete(
    "/expenses/{expense_id}"
)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):

    expense = db.query(Expense).filter(
        Expense.expense_id == expense_id,
        Expense.user_id == current_user.user_id
    ).first()

    if expense is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )


    db.delete(expense)
    db.commit()

    return {
        "message": "Expense deleted successfully",
        "expense_id": expense_id
    }


# ============================================================
# OVERALL AI ANALYSIS
# ============================================================

@app.get(
    "/ai/analyze"
)
def overall_ai_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):

    # --------------------------------------------------------
    # Today's date
    # --------------------------------------------------------

    today = date.today()


    # --------------------------------------------------------
    # Get user's expenses
    # --------------------------------------------------------

    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.user_id
    ).order_by(
        Expense.expense_date.desc()
    ).all()


    # ========================================================
    # CURRENT / ALREADY INCURRED EXPENSES
    # ========================================================

    current_month_expenses = [
        expense
        for expense in expenses
        if (
            expense.expense_date.year == today.year
            and expense.expense_date.month == today.month
            and expense.expense_date <= today
        )
    ]


    # ========================================================
    # FUTURE / PLANNED EXPENSES
    # ========================================================

    future_expenses = [
        expense
        for expense in expenses
        if expense.expense_date > today
    ]


    # --------------------------------------------------------
    # Current spending
    # --------------------------------------------------------

    total_spent = sum(
        (
            expense.amount
            for expense in current_month_expenses
        ),
        Decimal("0")
    )


    remaining_balance = (
        current_user.salary - total_spent
    )


    days_remaining = calculate_days_remaining(today)


    if days_remaining > 0:

        daily_spending_limit = (
            remaining_balance / Decimal(days_remaining)
        )

        if daily_spending_limit < 0:
            daily_spending_limit = Decimal("0")

    else:

        daily_spending_limit = Decimal("0")


    # --------------------------------------------------------
    # Future spending
    # --------------------------------------------------------

    future_expenses_total = sum(
        (
            expense.amount
            for expense in future_expenses
        ),
        Decimal("0")
    )


    projected_balance = (
        remaining_balance - future_expenses_total
    )


    # ========================================================
    # CATEGORY TOTALS
    # ========================================================

    category_totals = {}


    for expense in current_month_expenses:

        category = expense.category

        if category not in category_totals:

            category_totals[category] = Decimal("0")

        category_totals[category] += expense.amount


    # ========================================================
    # AI INPUT
    # ========================================================

    financial_data = {

        "user": {

            "name": current_user.name
        },

        "salary": str(
            current_user.salary
        ),

        "today": str(today),

        "current_month": {

            "days_remaining": days_remaining,

            "total_spent": str(
                total_spent
            ),

            "remaining_balance": str(
                remaining_balance
            ),

            "daily_spending_limit": str(
                daily_spending_limit
            ),

            "category_totals": {

                category: str(amount)

                for category, amount
                in category_totals.items()
            }
        },


        # ====================================================
        # FUTURE EXPENSES
        # ====================================================

        "future_expenses": {

            "count": len(
                future_expenses
            ),

            "total": str(
                future_expenses_total
            ),

            "projected_balance": str(
                projected_balance
            ),

            "expenses": [

                {
                    "title": expense.title,

                    "amount": str(
                        expense.amount
                    ),

                    "category": expense.category,

                    "description": expense.description,

                    "expense_date": str(
                        expense.expense_date
                    )

                }

                for expense in future_expenses
            ]
        },


        # ====================================================
        # ALL PREVIOUSLY INCURRED EXPENSES
        # ====================================================

        "previous_expenses": [

            {
                "title": expense.title,

                "amount": str(
                    expense.amount
                ),

                "category": expense.category,

                "description": expense.description,

                "expense_date": str(
                    expense.expense_date
                )

            }

            for expense in current_month_expenses
        ]
    }


    # ========================================================
    # CALL NEMOTRON
    # ========================================================

    try:

        result = analyze_expenses(
            financial_data
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI analysis unavailable: {str(e)}"
        )