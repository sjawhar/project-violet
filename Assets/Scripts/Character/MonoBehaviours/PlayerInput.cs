using UnityEngine;
using Gamekit2D;

namespace Buffalo
{
    public class PlayerInput : Gamekit2D.PlayerInput
    {
        public new static PlayerInput Instance
        {
            get { return s_Instance; }
        }

        protected new static PlayerInput s_Instance;

        void Awake()
        {
            if (Gamekit2D.PlayerInput.s_Instance == null)
            {
                Gamekit2D.PlayerInput.s_Instance = this;
            }
            else
            {
                throw new UnityException("There cannot be more than one PlayerInput script.  The instances are " + Gamekit2D.PlayerInput.s_Instance.name + " and " + name + ".");
            }

            if (s_Instance == null)
            {
                s_Instance = this;
            }
            else
            {
                throw new UnityException("There cannot be more than one PlayerInput script.  The instances are " + s_Instance.name + " and " + name + ".");
            }
        }

        void OnEnable()
        {
            if (Gamekit2D.PlayerInput.s_Instance == null)
            {
                Gamekit2D.PlayerInput.s_Instance = this;
            }
            else if (Gamekit2D.PlayerInput.s_Instance != this)
            {
                throw new UnityException("There cannot be more than one PlayerInput script.  The instances are " + Gamekit2D.PlayerInput.s_Instance.name + " and " + name + ".");
            }

            if (s_Instance == null)
            {
                s_Instance = this;
            }
            else if (s_Instance != this)
            {
                throw new UnityException("There cannot be more than one PlayerInput script.  The instances are " + s_Instance.name + " and " + name + ".");
            }

            PersistentDataManager.RegisterPersister(this);
        }

        void OnDisable()
        {
            PersistentDataManager.UnregisterPersister(this);

            Gamekit2D.PlayerInput.s_Instance = null;
            s_Instance = null;
        }


        public InputButton Dash = new InputButton(KeyCode.LeftShift, XboxControllerButtons.RightBumper);
        public InputButton DoubleJump = new DoubleTapButton(KeyCode.Space, XboxControllerButtons.A);

        protected override void GetInputs(bool fixedUpdateHappened)
        {
            Dash.Get(fixedUpdateHappened, inputType);
            DoubleJump.Get(fixedUpdateHappened, inputType);

            base.GetInputs(fixedUpdateHappened);
        }

        public override void GainControl()
        {
            base.GainControl();

            GainControl(Dash);
            GainControl(DoubleJump);
        }

        public override void ReleaseControl(bool resetValues = true)
        {
            base.ReleaseControl(resetValues);

            ReleaseControl(Dash, resetValues);
            ReleaseControl(DoubleJump, resetValues);
        }

        public void DisableDashing()
        {
            Dash.Disable();
        }

        public void EnableDashing()
        {
            Dash.Enable();
        }

        public new Data SaveData()
        {
            return new Data<bool, bool, bool>(MeleeAttack.Enabled, RangedAttack.Enabled, Dash.Enabled);
        }

        public new void LoadData(Data data)
        {
            Data<bool, bool, bool> playerInputData = (Data<bool, bool, bool>)data;

            if (playerInputData.value0)
                MeleeAttack.Enable();
            else
                MeleeAttack.Disable();

            if (playerInputData.value1)
                RangedAttack.Enable();
            else
                RangedAttack.Disable();

            if (playerInputData.value2)
                Dash.Enable();
            else
                Dash.Disable();
        }

        void OnGUI()
        {
            if (m_DebugMenuIsOpen)
            {
                const float height = 100;

                GUILayout.BeginArea(new Rect(30, Screen.height - height, 200, height));

                GUILayout.BeginVertical("box");
                GUILayout.Label("Press F12 to close");

                bool dashEnabled = GUILayout.Toggle(Dash.Enabled, "Enable Dash");
                bool meleeAttackEnabled = GUILayout.Toggle(MeleeAttack.Enabled, "Enable Melee Attack");
                bool rangeAttackEnabled = GUILayout.Toggle(RangedAttack.Enabled, "Enable Range Attack");

                if (dashEnabled != Dash.Enabled)
                {
                    if (dashEnabled)
                        Dash.Enable();
                    else
                        Dash.Disable();
                }

                if (meleeAttackEnabled != MeleeAttack.Enabled)
                {
                    if (meleeAttackEnabled)
                        MeleeAttack.Enable();
                    else
                        MeleeAttack.Disable();
                }

                if (rangeAttackEnabled != RangedAttack.Enabled)
                {
                    if (rangeAttackEnabled)
                        RangedAttack.Enable();
                    else
                        RangedAttack.Disable();
                }
                GUILayout.EndVertical();
                GUILayout.EndArea();
            }
        }
    }
}
